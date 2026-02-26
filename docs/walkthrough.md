# Multi-Insurer Product Catalog — Walkthrough

## What Changed

The D2C "Build Your Protection" section previously showed only **4 hardcoded life-insurance products** from a single anonymous source. It now displays **9 products from 3 distinct insurer tenants**, grouped visually by insurer.

### Backend (5 files)

| File                                                                                                            | Change                                                                                             |
| --------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| [underwrite.py](file:///c:/Users/PC/Documents/GitHub/heirs_insurance_hackathon/app/schemas/underwrite.py)       | Added `insurer_name` + `category` fields to `CoverageBlock`                                        |
| [underwrite.py](file:///c:/Users/PC/Documents/GitHub/heirs_insurance_hackathon/app/api/endpoints/underwrite.py) | Expanded `AVAILABLE_PRODUCTS` to 9 products across 3 insurers; updated `show_products` chat action |

### Frontend (3 files)

| File                                                                                                                                           | Change                                                                     |
| ---------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| [api.ts](file:///c:/Users/PC/Documents/GitHub/heirs_insurance_hackathon/frontend/d2c/src/services/api.ts)                                      | Added `insurerName` + `category` to `CoverageBlock` interface and mapper   |
| [CoverageSelector.tsx](file:///c:/Users/PC/Documents/GitHub/heirs_insurance_hackathon/frontend/d2c/src/components/policy/CoverageSelector.tsx) | Redesigned to group products by insurer with color-coded badges            |
| [PolicyBuilder.tsx](file:///c:/Users/PC/Documents/GitHub/heirs_insurance_hackathon/frontend/d2c/src/components/policy/PolicyBuilder.tsx)       | Schema inference now uses product `category` instead of ID string-matching |

## Product Catalog

| Insurer                     | Products                                              | Category  |
| --------------------------- | ----------------------------------------------------- | --------- |
| **Heirs Life Assurance**    | Life Protection, Critical Illness, Funeral Expenses   | Life      |
| **Heirs General Insurance** | Auto Comprehensive, Auto Third-Party, Home Protection | Auto/Home |
| **Heirs Gadget Insurance**  | Gadget Shield, Screen Protect, Extended Warranty      | Gadget    |

## Verification

- ✅ Backend restarted — `GET /products` returns 9 products with `insurer_name` fields
- ✅ D2C container rebuilt and deployed
- ✅ Browser verification confirmed horizontal category tabs working and product cards filtering correctly.

![Category Tabs Layout](file:///C:/Users/PC/.gemini/antigravity/brain/3c9550b0-adce-4eb7-98ab-7f9abdd1e1af/.system_generated/click_feedback/click_feedback_1771599082985.png)
