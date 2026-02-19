"""Debug script that writes ALL output directly to a log file."""
import asyncio
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "debug_log.txt")

def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

async def main():
    # Clear log file
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("=== Debug Underwrite Log ===\n\n")

    try:
        from app.core.config import settings
        log(f"1. GOOGLE_API_KEY loaded: {'YES (' + settings.GOOGLE_API_KEY[:10] + '...)' if settings.GOOGLE_API_KEY else 'NO'}")
    except Exception as e:
        log(f"1. FAILED to load settings: {e}")
        log(traceback.format_exc())
        return

    try:
        from app.db.session import AsyncSessionLocal
        from app.schemas.underwrite import UnderwriteRequest
        from app.services.underwriting import route_to_product, execute_underwriting
        log("2. Imports OK")
    except Exception as e:
        log(f"2. Import FAILED: {e}")
        log(traceback.format_exc())
        return

    async with AsyncSessionLocal() as db:
        req = UnderwriteRequest(
            age=35,
            product_type="life",
            role="consumer",
            holder_name="Test User",
            coverage_selection=[]
        )
        log("3. Request created")

        try:
            manual = await route_to_product(req, db)
            if manual:
                log(f"4. Manual found: product_type={manual.product_type}")
                log(f"5. Has compiled_rules: {bool(manual.compiled_rules)}")
                if manual.compiled_rules:
                    log(f"6. Rules preview (first 300 chars): {manual.compiled_rules[:300]}")
            else:
                log("4. NO MANUAL FOUND - this would cause 404")
                return
        except Exception as e:
            log(f"4. route_to_product FAILED: {e}")
            log(traceback.format_exc())
            return

        if not manual.compiled_rules:
            log("7. Manual has NO compiled rules - this would cause 503")
            return

        log("7. Calling execute_underwriting...")
        try:
            result = await execute_underwriting(req, manual)
            log(f"8. SUCCESS!")
            log(f"   Status: {result.status}")
            log(f"   Premium Monthly: {result.premium_monthly}")
            log(f"   Premium Annual: {result.premium_annual}")
            log(f"   Reason: {result.reason}")
            log(f"   Summary: {result.plain_english_summary}")
            log(f"   Policy Number: {result.policy_number}")
        except Exception as e:
            log(f"8. execute_underwriting FAILED!")
            log(f"   Error Type: {type(e).__name__}")
            log(f"   Error Message: {str(e)}")
            log(f"   Full Traceback:")
            log(traceback.format_exc())

    log("\n=== Done ===")

if __name__ == "__main__":
    asyncio.run(main())
    # Print location of log file so user knows where to look
    print(f"Log written to: {LOG_FILE}")
