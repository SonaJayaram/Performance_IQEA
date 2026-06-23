import openai
import os
from dotenv import load_dotenv

load_dotenv()
# api_key = os.getenv("AZURE_OPENAI_API_KEY")
# endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
# connect_string=os.getenv("AZURE_QUEUE_CONN_STRING")
os.environ["OPENAI_API_KEY"] = os.getenv("AZURE_OPENAI_API_KEY")
os.environ["OPENAI_API_BASE"] = os.getenv("AZURE_OPENAI_ENDPOINT")
print(os.environ["OPENAI_API_KEY"] )
print(os.environ["OPENAI_API_BASE"])
client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"],
                       base_url=os.environ["OPENAI_API_BASE"])


def get_queries_from_ai_updated(formatted_summary):
    print("going inside get_queries_from_ai_updated")
    model = "gpt-5-mini"
    try:
        response = client.chat.completions.create(model=model,
                                                  messages=[{"role": "user",
                                                             "content": formatted_summary
                                                             }
                                                            ])
        print(response)
        return response.choices[0].message.content
    except Exception as e:
        print(f"[ERROR] LLM call failed: {e}")
        return None


formatted_summary = """You are an expert QA test case generator. Your task is to produce exactly 20 end-to-end functional test cases in a clear, executable style based on the provided inputs.

Inputs:

- User Interaction Elements (Action Data): {'sauce_actions.txt': 'Switched to new window: [https://www.saucedemo.com/]\nClick on "login_credentials" (URL: https://www.saucedemo.com/)\nCopy on "login_credentials"\nClick on "user-name"\nShortcut_paste on "user-name"\nPaste on "user-name"\nEnter "standard_user" in the "user-name" field\nClick on "Password for all users:\nsecret_sauce"\nClick on "Password for all users:\nsecret_sauce"\nCopy on "Password for all users:\nsecret_sauce"\nClick on "password"\nShortcut_paste on "password"\nPaste on "password"\nEnter "secret_sauce" in the "password" field\nClick on "login-button"\nClick on "add-to-cart-sauce-labs-backpack" (URL: https://www.saucedemo.com/inventory.html)'}: complete navigation flow and actions (primary source — follow strictly in order, do not skip or jump). This contains all pages, clicks, fields, and intermediate steps.

Summary — Swag Labs (Sauce Labs) web app flow and key data

Entities
- Application: Swag Labs (Sauce Labs)
- Pages/screens: Login (home), Inventory, Cart, Checkout Step One (Your Information), Checkout Step Two (Overview), Checkout Complete (confirmation)
- UI elements: product list, sort dropdown (Name A→Z), Add to cart buttons, QTY/Description lines, form fields, payment/shipping summary, footer (Terms/Privacy, copyright)

Authentication
- Accepted usernames: standard_user, locked_out_user, problem_user, performance_glitch_user, error_user, visual_user
- Password for all users: secret_sauce
- Login action required to access inventory and shopping flow

Product catalog (examples shown)
- Sauce Labs Backpack
  - Description: "carry.allTheThings() with the sleek, streamlined Sly Pack that melds uncompromising style with unequaled laptop and tablet protection."
  - Price shown elsewhere: $29.99
- Sauce Labs Bolt T-Shirt
  - Description: testing superhero T-shirt; American Apparel; 100% ringspun combed cotton; heather gray with red bolt
  - Example price snippet: $15.99 (displayed as ¢15.99)
- Sauce Labs Bike Light
  - Description: red light; water-resistant; 3 lighting modes; 1 AAA battery included
- Sauce Labs Fleece Jacket
  - Description: midweight quarter-zip fleece jacket for outdoors/office
  - Example price snippet: displayed as ¢A9Q9 99 (garbled)
- Catalog features: product listing, descriptions, "Add to cart" action

Cart
- Cart page title: "Your Cart"
- Line item(s):
  - QTY: 1
  - Description: Sauce Labs Backpack (same description as product)
- Cart actions: view items, proceed to checkout

Checkout flow (sequence)
1. Checkout Step One — "Checkout: Your Information"
   - Required input fields: First Name, Last Name, Zip/Postal Code
   - Action: Continue to overview
2. Checkout Step Two — "Checkout: Overview"
   - Cart summary: QTY and Description (1 Sauce Labs Backpack)
   - Payment Information: "SauceCard #31337"
   - Shipping Information: "Free Pony Express Delivery!"
   - Price summary:
     - Item total: $29.99
     - Tax: $2.40
     - (Displayed total context: Price Total / possibly a final total)
   - Action: Finish / Complete order
3. Checkout Complete — confirmation
   - Message: "Thank you for your order! Your order has been dispatched, and will arrive just as fast as the pony can get there!"
   - Footer: © 2025 Sauce Labs. All Rights Reserved. Terms of Service | Privacy Policy

UI/test elements & behaviors useful for automation
- Login required; use provided test usernames and common password
- Product sorting option (Name A→Z)
- "Add to cart" buttons per product
- Cart displays QTY, description, supports proceeding to checkout
- Checkout step-one validates presence of First Name, Last Name, Zip/Postal Code
- Checkout overview shows payment method, shipping method, item totals and tax
- Completion shows dispatch confirmation text and footer links

Notable data points (for test cases)
- Use standard_user and other test accounts
- Password: secret_sauce
- Cart item: Sauce Labs Backpack, quantity 1
- Item price: $29.99; Tax: $2.40; Payment: SauceCard #31337; Shipping: Free Pony Express Delivery
- Confirmation copy: order dispatched + pony message
- Copyright year: 2025

Garbled/ambiguous text
- Some price strings in images are corrupted (e.g., "¢A9Q9 99", "Trak €99 90"); ignore or treat as non-authoritative for numeric validation

Sequence for automated test case
1. Log in with valid credentials (e.g., standard_user / secret_sauce)
2. Verify inventory loads and products are listed
3. Optionally sort products by name
4. Add "Sauce Labs Backpack" to cart
5. Open Cart, verify item (QTY=1, correct description)
6. Proceed to Checkout Step One; enter First Name, Last Name, Zip
7. Continue to Overview; verify item total $29.99, tax $2.40, payment "SauceCard #31337", shipping "Free Pony Express Delivery!"
8. Finish checkout; verify confirmation message and footer links

End of summary.: UI field names, labels, validation rules, page content.

Task: Generate end-to-end test cases from the provided action flow.
Objective:
Each test case = one complete user journey (positive or negative, not mixed).
Cover all major workflows:
Login
Inventory
Cart
Checkout
logout
Granularity Rules:
Test Case Granularity: Each scenario type (positive/negative) = separate test case.
Include full navigation and data entry from start to finish.
Test Step Granularity: Each user action = one step (click, type, select, switch).
Break navigation into individual clicks (e.g., "Click 'About Us'" → "Click 'Leadership'").
Each form field input = separate step.
Order & Coverage: Follow the exact chronological order of the provided action file.
Do not skip or reorder steps.
Ensure all scenarios are covered.: user stories, acceptance criteria, business rules.

Mandatory Rules:

1. Generate exactly 20 unique test cases that cover all flows, pages, actions, clicks, and form fields present in action_data_processed. Do not omit any step, intermediate click, or input.

2. Each Test Case must represent one complete user journey (positive or negative).
   - Example: One test case for successful form submission, another for negative validations.
   - Do not mix positive and negative scenarios in the same test case.

Step Writing Style & URL Rules:

- Steps must be human-readable and executable by a manual tester.
- Do not explicitly mention page names; derive context from action_data_processed.
- Use these patterns for actions:
    - Launch the application and open <URL> ← only for the first action on a page.
    - Click on "<UI label>" ← if the click changes the URL, include the new URL in the expected result; otherwise, omit URL.
    - Enter "<value>" in "<field>" field ← no URL needed.
    - Select "<option>" from "<dropdown>" ← no URL needed.
    - Verify visibility of "<fields/sections>" ← no URL needed.
    - Switch to window with URL "<URL>" ← include URL when switching windows.
- Every navigation and intermediate step must be included — no shortcuts.
- For validation steps:
    - Leave "<field>" empty and click "<button>" → Expect validation error message
    - Enter "<invalid value>" in "<field>" → Expect validation error message

Test Case Naming:

- Use sequential unique names: TC01 - <title> to TC20 - <title>.
- Keep titles short and descriptive.

Expected Results:

- Every input, click, or submission must have a clear expected result.
- Validation failures must show the exact error text if available; otherwise, describe the expected error clearly.

Coverage:

- Cover all flows, pages, actions, and form fields present in action_data_processed.
- Each form field must have at least one positive and one negative validation across the suite.
- Include navigation, content verification, and boundary conditions.

Output Format:

- A single Markdown table with this exact header:
  | Test Case Name | Step Number | Test Step Description | Test Step Expected Result | Status | Type | Category
- Category can be Positive, Negative, Workflow, Edge case, UI, etc..
- Write the Category only in Step 0 (the prerequisite/background step). Leave it blank
- Status = New; Type = Manual for every row;
- Step numbers restart for each test case (0,1,2,…). Step 0 = Prerequisite/Background.
- Each test case must have at least 6 steps.

Strict Constraint:

- Do not truncate, summarize, or insert placeholders like “[continued]”.
- Generate the full table with exactly 10 test cases, each fully written out.
- Follow the step style strictly (plain actions, human-readable, no “page — field — action” format).
- Ensure every scenario from the provided action file is captured exactly; do not miss any page, click, form, or intermediate interaction."""
get_queries_from_ai_updated(formatted_summary)