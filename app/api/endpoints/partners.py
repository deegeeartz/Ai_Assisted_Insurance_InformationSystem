from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.services.auth import get_current_user
from app.models.core import User, Policy, Payment, UserRole
from app.models.audit import AuditLog, UnderwritingDecisionLog
import csv
import io
import json

router = APIRouter()

@router.get("/dashboard")
async def get_partner_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get aggregated metrics for the partner:
    - Total Policies Sold
    - Total Commission Earned
    - Recent Transactions
    """
    if current_user.role != UserRole.PARTNER:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Metrics
    policies_res = await db.execute(select(Policy).where(Policy.partner_id == current_user.id))
    policies = policies_res.scalars().all()
    total_policies = len(policies)
    
    total_commission = 0
    recent_transactions = []
    
    if policies:
        pol_ids = [p.id for p in policies]
        # Fetch successful payments for these policies
        pay_res = await db.execute(select(Payment).where(Payment.policy_id.in_(pol_ids), Payment.status == "success"))
        payments = pay_res.scalars().all()
        
        # Create a dictionary for quick policy lookup to get the policy_number
        policy_map = {p.id: p.policy_number for p in policies}
        
        for payment in payments:
            total_commission += payment.partner_commission
            recent_transactions.append({
                "policy_id": policy_map.get(payment.policy_id, "Unknown"),
                "amount": payment.amount,
                "commission": payment.partner_commission,
                "date": payment.created_at
            })

    # Sort transactions by date desc
    recent_transactions.sort(key=lambda x: x['date'], reverse=True)

    api_key = current_user.api_key or ""
    if api_key:
        # Never return the full key in routine reads; the portal shows the full
        # key only once, in the response of POST /partners/api-key/rotate.
        api_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 16 else f"{api_key[:4]}..."

    return {
        "metrics": {
            "total_policies_sold": total_policies,
            "total_commission_earned": round(total_commission, 2),
            "currency": "NGN"
        },
        "recent_transactions": recent_transactions[:10],
        "api_key": api_key  # Masked — for display in portal
    }

@router.post("/api-key/rotate")
async def rotate_api_key(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Regenerate the Partner's API Key"""
    if current_user.role != UserRole.PARTNER:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    import secrets
    new_key = f"ib_sk_{secrets.token_urlsafe(32)}"
    current_user.api_key = new_key
    
    db.add(AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        action="rotate_api_key",
        resource_type="user",
        resource_id=current_user.email,
    ))

    await db.commit()
    
    return {"api_key": new_key}

@router.post("/batch-underwrite")
async def batch_underwrite(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Tier 3 B2B Integration: Bulk CSV Issuance.
    Accepts a standard CSV file with headers matching UnderwriteRequest fields.
    Processes each row programmatically and attempts to bind policies.
    """
    if current_user.role != UserRole.PARTNER:
        raise HTTPException(status_code=403, detail="Only partners can bulk underwrite.")

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported.")

    content = await file.read()
    try:
        decoded = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(decoded))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read CSV: {str(e)}")

    from app.schemas.underwrite import UnderwriteRequest
    from app.services.underwriting import route_to_product, execute_underwriting

    results = {
        "total_rows": 0,
        "approved": 0,
        "declined": 0,
        "failed": 0,
        "total_premium": 0.0,
        "logs": []
    }

    for row in reader:
        results["total_rows"] += 1
        try:
            # Basic mapping from CSV to UnderwriteRequest
            req = UnderwriteRequest(
                age=int(row.get("age", 30)),
                product_type=row.get("product_type", "life"),
                holder_name=row.get("holder_name", "CSV Upload"),
                holder_email=row.get("holder_email", current_user.email),
                coverage_selection=[] 
            )
            
            # Handle coverage array correctly if serialized
            cov_str = row.get("coverage_selection")
            if cov_str:
                try:
                    req.coverage_selection = json.loads(cov_str.replace("'", '"'))
                except (json.JSONDecodeError, TypeError, ValueError):
                    # Fallback to empty if bad valid json in csv
                    pass

            manual = await route_to_product(req, db)
            if not manual:
                results["failed"] += 1
                results["logs"].append(f"Row {results['total_rows']}: Product '{req.product_type}' not found.")
                continue

            from app.services.tenant import policy_tenant_from_product
            decision = await execute_underwriting(req, manual)



            from app.services.underwriting import bind_policy_from_decision
            
            decision_log, new_policy = await bind_policy_from_decision(
                decision=decision,
                request=req,
                manual=manual,
                db=db,
                channel="batch",
                partner_id=current_user.id
            )
            # The partner API currently waits until all rows are processed,
            # but db is scoped to the request. We don't commit per row, just let the router commit at the end?
            # Actually, batch processing should probably wait to commit. We just don't commit here.
            # But bind_policy_from_decision does db.add.

            if new_policy:
                results["approved"] += 1
                results["total_premium"] += (decision.premium_annual or 0.0)
                results["logs"].append(f"Row {results['total_rows']}: Approved -> {new_policy.policy_number}")
            else:
                results["declined"] += 1
                results["logs"].append(f"Row {results['total_rows']}: Declined -> {decision.reason}")

        except Exception as e:
            results["failed"] += 1
            results["logs"].append(f"Row {results['total_rows']}: Error -> {str(e)}")

    db.add(AuditLog(
        user_id=current_user.id,
        user_email=current_user.email,
        action="batch_underwrite",
        resource_type="batch_job",
        resource_id=file.filename,
        details=f"rows: {results['total_rows']}, approved: {results['approved']}, declined: {results['declined']}",
    ))

    await db.commit()
    return results
