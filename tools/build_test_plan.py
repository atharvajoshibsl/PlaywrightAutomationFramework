"""Build TEST_PLAN.xlsx from the case lists below.

    py tools/build_test_plan.py

Edit cases here and re-run. Close Excel first (write lock).
"""

from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

OUT = Path(__file__).resolve().parent.parent / "TEST_PLAN.xlsx"

# Row shape: id, name, area, suite, scope, priority, pre, steps, expected.
# Suite = lowest tier; scope = Feature, End-to-End, or Negative.

FRESH = ("Shop reset to its starting state: 16 products, 53 variants, "
         "2 accounts, no orders")
SIGNED_IN = ("Signed in as demo@shop.test / Demo@123, shop at its starting "
             "state")
AWAITING = "An order has been placed and is waiting to be paid"
PAID = "An order has just been paid for"

CASES = [
    # -------------------------------------------------------------- interface
    ("TC01", "Home page renders the full expected interface",
     "Interface", "Smoke", "Feature", "P1", FRESH,
     "1. Open the site root.\n"
     "2. Inspect the header: wordmark, tagline, search box, theme toggle, "
     "cart link with count, Sign in and Register links.\n"
     "3. Inspect the filter and sort controls: all four category filters and "
     "every sort option.\n"
     "4. Inspect the result count and the anatomy of one product card: "
     "image, brand, name, price, rating, stock badge.\n"
     "5. Inspect the footer: framework list and copyright line.",
     "Every element is present and populated, and the count reads 16 "
     "products found. This is the only interface-rendering case in the plan; "
     "every other case asserts behaviour, not presence."),

    # -------------------------------------------------------------- catalogue
    ("TC02", "Catalogue search, clear, category filter and sort",
     "Catalogue", "Smoke", "Feature", "P1", FRESH,
     "1. Open the site root and confirm the count reads 16 products found.\n"
     "2. Search for 'sandal'; confirm only Trail Sandals is listed and the "
     "count reads 1.\n"
     "3. Clear the search box using the Clear control; confirm all 16 "
     "products return and the box is empty.\n"
     "4. Select each category in turn (Apparel, Electronics, Footwear, "
     "Home & Kitchen); confirm each listing holds only that category and the "
     "four counts add up to 16.\n"
     "5. With Footwear active, choose Price: low to high without clicking "
     "any other control; confirm prices are non-decreasing.\n"
     "6. Choose Price: high to low; confirm prices are non-increasing.\n"
     "7. With Footwear and a sort still active, search for 'shoes'; confirm "
     "results stay Footwear-only, still sorted, and both selections remain "
     "in the form.\n"
     "8. Search for 'zzzzqx'; confirm the empty state appears with a count "
     "of 0 and no error page.",
     "Every step behaves as described. Two regression guards live here: "
     "clearing the search used to leave the filtered listing in place, and "
     "searching used to drop the category and sort. The sort dropdown submits "
     "on change alone, so automation must wait on navigation rather than on a "
     "load state."),

    # ---------------------------------------------------------- product detail
    ("TC03", "Product detail opens from a card and adds to the cart",
     "Product detail", "Smoke", "Feature", "P1", FRESH,
     "1. On the home page, note the name and price shown on the Mechanical "
     "Keyboard card.\n"
     "2. Click the card.\n"
     "3. Confirm the URL carries the product slug and that name and price "
     "match the card, and that brand, rating, description, variant selector "
     "and Add to cart are all present.\n"
     "4. Note the header cart count.\n"
     "5. Select an in-stock variant and add it to the cart.",
     "The detail page matches the card exactly, the header cart count "
     "increases by one, and a confirmation is shown."),

    # -------------------------------------------------------------------- cart
    ("TC04", "Cart quantities, line totals and clearing",
     "Cart", "Smoke", "Feature", "P1", FRESH,
     "1. Add Wireless Mouse (Standard) to the cart and open the cart.\n"
     "2. Confirm the line total equals unit price x quantity, and the "
     "subtotal equals the sum of line totals.\n"
     "3. Change the quantity field to 3 and confirm nothing changes yet.\n"
     "4. Press Update.\n"
     "5. Confirm the line total is three times the unit price and the "
     "subtotal follows.\n"
     "6. Use Clear cart.",
     "Arithmetic is exact to the rupee at every step, totals change only "
     "once Update is pressed, and clearing leaves the empty state with a "
     "header count of zero."),

    # ---------------------------------------------------------- authentication
    ("TC05", "Sign in, sign out and registration",
     "Authentication", "Sanity", "Feature", "P1", FRESH,
     "1. Sign in as demo@shop.test / Demo@123.\n"
     "2. Confirm the header shows the signed-in state with the account "
     "holder's name.\n"
     "3. Sign out; confirm Sign in and Register return and account-only "
     "pages are no longer reachable.\n"
     "4. Register a new account using an email that is not already in use.",
     "Sign-in, sign-out and registration all succeed, and the new account "
     "lands signed in with a wallet balance of zero."),

    ("TC06", "Login rejects bad credentials without revealing which",
     "Authentication", "Sanity", "Negative", "P2", FRESH,
     "1. Attempt sign-in with demo@shop.test and a wrong password; record "
     "the message.\n"
     "2. Attempt sign-in with an email that has no account; record the "
     "message.\n"
     "3. Submit the login form with both fields empty.\n"
     "4. Attempt to register using demo@shop.test, an address already in "
     "use.",
     "The first two failures use identical wording, so the form cannot be "
     "used to discover which emails have accounts. The empty form is refused "
     "by validation, the duplicate registration is refused without creating a "
     "second account, and no session is created in any case."),

    # ------------------------------------------------------------- guest flow
    ("TC07", "Guest cart survives sign-in and login returns the guest to "
             "their page",
     "Guest flow", "Sanity", "End-to-End", "P1", FRESH,
     "1. As a guest, add two different products to the cart.\n"
     "2. Navigate to the orders page; confirm you are sent to login and the "
     "URL carries a next parameter.\n"
     "3. Sign in as demo@shop.test.\n"
     "4. Confirm you land on the orders page you originally asked for.\n"
     "5. Open the cart; confirm both guest lines are present with their "
     "quantities and totals intact.\n"
     "6. Sign out, add one product as a guest, then register a new account.\n"
     "7. Open the cart.",
     "The guest cart follows the visitor into an existing account and into a "
     "newly registered one, and an interrupted guest is returned to the page "
     "they asked for rather than dumped on the home page."),

    # ---------------------------------------------------------------- checkout
    ("TC08", "Checkout summary is accurate and places the order",
     "Checkout", "Sanity", "Feature", "P1", SIGNED_IN,
     "1. Add an item to the cart and proceed to checkout.\n"
     "2. Confirm the account's default saved address is preselected.\n"
     "3. Confirm the order summary matches the cart line by line, including "
     "delivery.\n"
     "4. Place the order.",
     "An order number is issued, the order is waiting to be paid, and the "
     "payment page opens for it."),

    ("TC09", "Checkout is refused with an empty cart",
     "Checkout", "Regression", "Negative", "P2", SIGNED_IN,
     "1. Make sure the cart is empty.\n"
     "2. Navigate directly to the checkout URL.",
     "Checkout is refused or redirects to the cart, and no empty order is "
     "created."),

    # ----------------------------------------------------------------- payment
    ("TC10", "Card payment: decline, expiry and successful retry",
     "Payment", "Sanity", "Feature", "P1", AWAITING,
     "1. On the Card tab, pay with 4000 0000 0000 0002; confirm a clear "
     "decline and that the order still exists and remains payable.\n"
     "2. Pay with 4000 0000 0000 0069; confirm it fails specifically as "
     "expired rather than as a generic decline.\n"
     "3. Pay with 4111 1111 1111 1111, a future expiry and any three-digit "
     "CVV.\n"
     "4. Open order history.",
     "The retry is approved, the same order becomes paid exactly once, no "
     "duplicate order is created, and a failed payment never loses the "
     "basket."),

    ("TC11", "UPI payment approves after its window and declines on failure",
     "Payment", "Sanity", "Feature", "P1", AWAITING,
     "1. On the UPI tab, submit fail@upi; confirm an immediate decline with "
     "no processing wait.\n"
     "2. Submit success@upi; confirm the order reports processing.\n"
     "3. Wait on the status page.",
     "The order becomes paid after roughly three seconds. The flip cannot be "
     "rushed, so the test must wait for the state to change rather than sleep "
     "a fixed time. This is the one place a real wait is unavoidable."),

    ("TC12", "Wallet payment succeeds on sufficient funds and is refused "
             "otherwise",
     "Payment", "Sanity", "Feature", "P1", AWAITING,
     "1. Force the wallet below the order total and attempt to pay from the "
     "wallet.\n"
     "2. Confirm the payment is refused, the balance is untouched, and the "
     "order is still payable by another method.\n"
     "3. Force the wallet above the order total and pay from the wallet.",
     "The order becomes paid and the wallet balance falls by exactly the "
     "order total."),

    # ------------------------------------------------------------------ orders
    ("TC13", "Order history and detail match what was bought",
     "Orders", "Sanity", "Feature", "P1", PAID,
     "1. Open order history and find the most recent order; confirm its "
     "number, date, total and paid status.\n"
     "2. Open the order.\n"
     "3. Compare it against what checkout showed.",
     "Items, quantities, unit prices, discount, delivery, grand total and "
     "delivery address all match exactly."),

    ("TC14", "Another account's order is not reachable",
     "Orders", "Regression", "Negative", "P2",
     "An order number belonging to a different account",
     "1. Note an order number that belongs to another account.\n"
     "2. Sign in as a different user.\n"
     "3. Navigate directly to that order's detail URL.",
     "The order is reported as not found or access is refused. No detail is "
     "leaked."),

    # ----------------------------------------------------------------- profile
    ("TC15", "Profile details and address book",
     "Profile", "Regression", "End-to-End", "P2", SIGNED_IN,
     "1. On the profile page, change the full name and phone number and "
     "save.\n"
     "2. Reload; confirm both persist and the header greeting shows the new "
     "name.\n"
     "3. Add a new address to the address book.\n"
     "4. Add an item to the cart, proceed to checkout and select the new "
     "address.\n"
     "5. Place the order.",
     "Details persist across a reload, and the new address appears in the "
     "book, can be chosen at checkout, and is recorded on the placed order."),

    # ---------------------------------------------------------------- test api
    ("TC16", "Health and reset return a known starting state",
     "Test API", "Smoke", "Feature", "P1", FRESH,
     "1. Send a GET to the health endpoint; confirm 200 and counts of 16 "
     "products, 53 variants, 2 accounts and no orders.\n"
     "2. Change data through the interface: add cart items and place an "
     "order.\n"
     "3. Send a POST to the reset endpoint on the same cookie jar as the "
     "browser.\n"
     "4. Re-read the health counts and the cart.",
     "Counts return to the starting values and the cart is empty. Nothing "
     "else in the framework is trustworthy until this passes, and health "
     "doubles as a readiness probe before a suite starts."),

    ("TC17", "Each visitor is isolated from another's reset",
     "Test API", "Sanity", "Feature", "P1", FRESH,
     "1. In browser context A, add items to the cart.\n"
     "2. In browser context B, add different items and call reset.\n"
     "3. Re-read context A's cart.",
     "Context A is untouched. Every visitor gets their own copy of the shop, "
     "which is what makes parallel test runs and a public demo safe."),

    # --------------------------------------------------------------- framework
    ("TC18", "Self-healing suggests fixes for stale locators",
     "Framework", "Regression", "Feature", "P3", FRESH,
     "1. Ask for six home page elements through the healing wrapper: two by "
     "their real test ids, three by ids the application no longer uses, and "
     "one for a control the page does not have at all.\n"
     "2. Let the six visibility checks run and record their outcomes.\n"
     "3. Read the page's elements once and ask the model only about the ids "
     "that are missing.\n"
     "4. Try each suggested locator against the live page.",
     "The two real ids pass and cost nothing. Each renamed id gets a whole "
     "locator expression, verified to resolve to exactly one element, with "
     "the file and line to change; the absent control gets no suggestion and "
     "is called out as a possible defect instead. Suggestions appear in the "
     "terminal and as an Allure attachment. The case is marked xfail because "
     "its failures are the demonstration."),
]

# Deferred cases; TCF_ prefix keeps them out of the working set.
FUTURE = [
    ("TCF_01", "Delivery fee and the free-delivery threshold",
     "Cart", "Sanity", "Feature", "P3", FRESH,
     "1. Add a single item priced under Rs 2,000 and open the cart.\n"
     "2. Confirm delivery is Rs 49 and the grand total equals subtotal "
     "plus 49.\n"
     "3. Add items until the payable amount reaches Rs 2,000 or more.\n"
     "4. Re-read the summary.",
     "Delivery becomes free at or above Rs 2,000 and the grand total then "
     "equals the subtotal."),

    ("TCF_02", "Coupons apply, cap and reject correctly",
     "Checkout", "Sanity", "Feature", "P3", SIGNED_IN,
     "1. Build a cart with a known subtotal and apply SAVE10; confirm the "
     "discount is ten percent, rounded to the rupee.\n"
     "2. Build a cart whose ten percent would exceed Rs 500 and apply "
     "SAVE10; confirm the discount caps at Rs 500.\n"
     "3. Build a cart above Rs 1,000 and apply FLAT200; confirm exactly "
     "Rs 200 comes off.\n"
     "4. Build a cart at or below Rs 1,000 and apply FLAT200; confirm it is "
     "refused with a message naming the minimum and the total is unchanged.\n"
     "5. Apply EXPIRED to any cart; confirm it is refused and the total is "
     "unchanged.\n"
     "6. Build a cart just over Rs 2,000 with free delivery, then apply "
     "SAVE10 so the payable amount falls below Rs 2,000.",
     "Each coupon behaves as described. In step 6 the Rs 49 delivery fee "
     "reappears, because the free-delivery threshold is evaluated after the "
     "discount. That ordering is deliberate and is the highest-value "
     "assertion in the pricing rules."),

    ("TCF_03", "Stock is consumed on payment, not on add to cart",
     "Payment", "Sanity", "End-to-End", "P3", SIGNED_IN,
     "1. Record a variant's stock level.\n"
     "2. Add it to the cart; confirm the stock is unchanged.\n"
     "3. Place the order; confirm the stock is still unchanged.\n"
     "4. Pay successfully and re-read the stock.",
     "Stock only decreases once payment succeeds, so an abandoned checkout "
     "never holds inventory."),

    ("TCF_04", "Cancelling refunds, reverses cashback and restores stock, but "
               "is blocked once shipped",
     "Orders", "Sanity", "End-to-End", "P3", PAID,
     "1. Note the wallet balance, the order total and the variant's stock "
     "after payment.\n"
     "2. Cancel the order.\n"
     "3. Re-read the wallet, the wallet ledger and the variant's stock.\n"
     "4. Place and pay for a second order, advance it to shipped using the "
     "test endpoint, then attempt to cancel it.",
     "The first order is cancelled, the wallet rises by the full order "
     "total, a debit reverses the cashback, the ledger still sums to the "
     "displayed balance, and stock returns to its pre-purchase level. The "
     "shipped order cannot be cancelled and stays shipped — a state only "
     "reachable through the advance endpoint, since fulfilment would "
     "otherwise take days."),

    ("TCF_05", "Wallet balance, top-up and ledger reconciliation",
     "Wallet", "Sanity", "Feature", "P3", SIGNED_IN,
     "1. Open the wallet; confirm the starting balance reads Rs 5,000.\n"
     "2. Top up Rs 500 with the succeeding demo card; confirm the balance "
     "rises by exactly Rs 500 and one credit row is added.\n"
     "3. Buy and pay for an item, then return to the wallet; confirm a "
     "cashback credit row for two percent of the paid total.\n"
     "4. Cancel that order; confirm a refund credit row for the order total "
     "and a debit reversing the cashback.\n"
     "5. Read every ledger row and sum the credits and debits from zero.",
     "The sum equals the displayed balance, and each row's recorded "
     "balance-after matches the running total. This is the strongest "
     "invariant in the app and is worth asserting after any test that moves "
     "money."),

    ("TCF_06", "Password change takes effect and rejects a wrong current "
               "password",
     "Profile", "Regression", "End-to-End", "P3", SIGNED_IN,
     "1. Attempt a password change supplying an incorrect current password; "
     "confirm it is refused.\n"
     "2. Change the password supplying the correct current password.\n"
     "3. Sign out.\n"
     "4. Sign in with the new password, then attempt the old one.",
     "The wrong-current-password attempt is refused and the existing "
     "password keeps working. After the real change the new password works "
     "and the old one is refused."),

    ("TCF_07", "State-forcing endpoints are reflected in the interface",
     "Test API", "Regression", "Feature", "P3", SIGNED_IN,
     "1. Force a variant's stock to zero, then open that product's detail "
     "page; confirm it shows as out of stock and cannot be added.\n"
     "2. Force the wallet to a chosen amount, then open the wallet; confirm "
     "the balance matches and the ledger still reconciles.\n"
     "3. Call the advance endpoint repeatedly on a paid order, reading the "
     "status after each call.",
     "Each forced state shows up in the interface, and the status moves "
     "placed, packed, shipped, delivered before stopping at delivered. These "
     "endpoints are how a test arranges out-of-stock, low-balance and shipped "
     "states without buying inventory down or waiting days."),

    ("TCF_08", "Guest buys, recovers from a declined card and verifies the "
               "order",
     "End-to-end", "Smoke", "End-to-End", "P3", FRESH,
     "1. As a guest, browse the catalogue and open a product.\n"
     "2. Add an in-stock variant to the cart.\n"
     "3. Sign in as demo@shop.test and confirm the cart carried over.\n"
     "4. Apply SAVE10 at checkout and place the order.\n"
     "5. Pay with the declining card and confirm the failure.\n"
     "6. Retry with the succeeding card.\n"
     "7. Open order history, then the order detail.\n"
     "8. Check the variant's stock and the wallet.",
     "The order is paid exactly once, totals match what checkout showed, "
     "stock has dropped, and cashback has landed in the wallet."),

    ("TCF_09", "Wallet purchase cancelled for a full refund",
     "End-to-end", "Sanity", "End-to-End", "P3", SIGNED_IN,
     "1. Note the wallet balance.\n"
     "2. Buy an item and pay from the wallet.\n"
     "3. Confirm the balance fell by the total and rose by the cashback.\n"
     "4. Cancel the order.\n"
     "5. Re-read the wallet, the ledger and the variant's stock.",
     "The refund credits the full total, the cashback is reversed, stock is "
     "restored, and the ledger sums to the displayed balance at every step "
     "along the way."),
]

# Cases that have a test file under tests/.
AUTOMATED = {"TC01", "TC02", "TC03", "TC04", "TC05", "TC06", "TC07", "TC08",
             "TC09", "TC10", "TC18"}

HEADERS = [
    ("Test Case ID", 12),
    ("Feature Area", 16),
    ("Suite", 12),
    ("Scope", 12),
    ("Priority", 9),
    ("Test Case Name", 52),
    ("Preconditions", 34),
    ("Steps", 66),
    ("Expected Result", 66),
    ("Automation Status", 17),
    ("Notes", 22),
]

# Source order differs from sheet order; COLUMN_ORDER maps columns out.
COLUMN_ORDER = [0, 2, 3, 4, 5, 1, 6, 7, 8]
SUITE_COLUMN = COLUMN_ORDER.index(3)
SCOPE_COLUMN = COLUMN_ORDER.index(4)

HEADER_FILL = PatternFill("solid", fgColor="1F3864")
FUTURE_HEADER_FILL = PatternFill("solid", fgColor="5A5A6E")
BANNER_FILL = PatternFill("solid", fgColor="EDE7F6")
BAND_FILL = PatternFill("solid", fgColor="F2F5FA")
SMOKE_FILL = PatternFill("solid", fgColor="FFF2CC")
NEGATIVE_FILL = PatternFill("solid", fgColor="FCE4E4")
THIN = Side(style="thin", color="D0D7E5")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def header_row(ws, fill):
    ws.append([name for name, _ in HEADERS])
    for cell in ws[ws.max_row]:
        cell.font = Font(bold=True, color="FFFFFF", size=11)
        cell.fill = fill
        cell.alignment = Alignment(vertical="center", horizontal="center",
                                   wrap_text=True)
        cell.border = BORDER
    ws.row_dimensions[ws.max_row].height = 30


def case_rows(ws, cases, status, note):
    for index, case in enumerate(cases):
        # Cases with a test file report Automated; the rest keep the default.
        state = "Automated" if case[0] in AUTOMATED else status
        ws.append([case[i] for i in COLUMN_ORDER] + [state, note])
        row = ws[ws.max_row]
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)
            cell.border = BORDER
            if index % 2:
                cell.fill = BAND_FILL
        # Highlight Smoke and Negative so they stand out in the sheet.
        if case[3] == "Smoke":
            row[SUITE_COLUMN].fill = SMOKE_FILL
            row[SUITE_COLUMN].font = Font(bold=True)
        if case[4] == "Negative":
            row[SCOPE_COLUMN].fill = NEGATIVE_FILL
            row[SCOPE_COLUMN].font = Font(bold=True)
        row[0].font = Font(bold=True)


def write_cases(ws):
    header_row(ws, HEADER_FILL)
    case_rows(ws, CASES, "Not started", "")
    active_last = ws.max_row

    # Autofilter covers CASES only, not deferred rows below.
    ws.auto_filter.ref = f"A1:{get_column_letter(len(HEADERS))}{active_last}"

    ws.append([])
    ws.append([f"FUTURE SCOPE — deferred to a later phase ({len(FUTURE)} "
               f"cases)"])
    banner = ws[ws.max_row]
    banner[0].font = Font(bold=True, size=12, color="4A148C")
    for column in range(len(HEADERS)):
        banner[column].fill = BANNER_FILL
    ws.row_dimensions[ws.max_row].height = 22

    header_row(ws, FUTURE_HEADER_FILL)
    case_rows(ws, FUTURE, "Deferred", "Future scope")

    for column, (_, width) in enumerate(HEADERS, start=1):
        ws.column_dimensions[get_column_letter(column)].width = width

    ws.freeze_panes = "C2"

    status = DataValidation(
        type="list",
        formula1='"Not started,In progress,Automated,Manual only,Blocked,'
                 'Deferred"',
        allow_blank=True,
    )
    ws.add_data_validation(status)
    status.add(f"J2:J{ws.max_row}")


def write_reference(ws):
    def block(title, headers, rows):
        ws.append([])
        ws.append([title])
        ws[ws.max_row][0].font = Font(bold=True, size=12, color="1F3864")
        ws.append(headers)
        for cell in ws[ws.max_row]:
            if cell.value:
                cell.font = Font(bold=True)
                cell.fill = PatternFill("solid", fgColor="E8EDF5")
        for row in rows:
            ws.append(row)

    ws.append(["AItomationKart — test data and conventions"])
    ws["A1"].font = Font(bold=True, size=14, color="1F3864")

    block("Starting state, after a reset", ["Entity", "Count"],
          [["Products", 16], ["Variants", 53], ["Accounts", 2],
           ["Orders", 0]])

    block("Demo accounts", ["Email", "Password", "Wallet"],
          [["demo@shop.test", "Demo@123", "Rs 5,000"],
           ["empty@shop.test", "Demo@123", "Rs 0"]])

    block("Demo cards", ["Card number", "Outcome"],
          [["4111 1111 1111 1111", "Succeeds"],
           ["4000 0000 0000 0002", "Declined by the issuer"],
           ["4000 0000 0000 0069", "Reported as expired"],
           ["Any other valid number", "Succeeds"]])

    block("Demo UPI", ["VPA", "Outcome"],
          [["success@upi", "Approved after roughly 3 seconds"],
           ["fail@upi", "Declined immediately"],
           ["Any other valid VPA", "Succeeds"]])

    block("Coupons", ["Code", "Effect"],
          [["SAVE10", "10% off, capped at Rs 500"],
           ["FLAT200", "Rs 200 off orders over Rs 1,000"],
           ["EXPIRED", "Always rejected"]])

    block("Money rules", ["Rule", "Detail"],
          [["Delivery fee", "Rs 49"],
           ["Free delivery threshold", "Rs 2,000 payable"],
           ["Threshold evaluated", "After discount, so a coupon can restore "
                                   "the fee"],
           ["Cashback", "2% of the paid total, credited to the wallet"],
           ["Cancellation", "Refunds the full total and reverses cashback"],
           ["Storage", "Whole rupees in INTEGER columns, no floats"]])

    block("Order states", ["Flow", "States"],
          [["Fulfilment", "PENDING > PLACED > PACKED > SHIPPED > DELIVERED"],
           ["Cancellable from", "PENDING, PLACED or PACKED only"],
           ["Payment", "PENDING > PROCESSING > PAID > REFUNDED, or FAILED"]])

    block("Suite meaning", ["Suite", "When it runs"],
          [["Smoke", "Every run and every deploy. Does the app work at all"],
           ["Sanity", "After a change to a feature. Includes Smoke"],
           ["Regression", "Full suite before a release. Includes everything"]])

    block("Scope meaning", ["Scope", "What it means"],
          [["Feature", "Behaviour of one feature or page"],
           ["End-to-End", "Crosses feature boundaries, following a journey"],
           ["Negative", "The point of the case is that bad input is "
                        "rejected"]])

    block("Case id prefixes", ["Prefix", "Meaning"],
          [["TC..", "In the working set. Being automated in this phase"],
           ["TCF_..", "Future scope. Written up, deferred to a later phase"]])

    block("Conventions", ["Decision", "Rationale"],
          [["One case per page or flow",
            "Checks on the same page are steps inside one case, not separate "
            "cases"],
           ["Reset before every test",
            "Rebuilds only the caller's data, so tests can run in parallel"],
           ["Reset shares the browser cookie jar",
            "A separate request context resets a different sandbox"],
           ["Totals computed in the test",
            "Integers make exact assertions possible, so never read a total "
            "off the page and compare it to itself"],
           ["No fixed sleeps",
            "Only UPI approval and the sort dropdown need a real wait, and "
            "both wait on a state change"],
           ["Hosted target by default",
            "Runs go against https://atharvajoshi.pythonanywhere.com. Local "
            "is available via BASE_URL when debugging a change"]])

    block("Not in the plan at all", ["Area", "Why"],
          [["Interface rendering per element",
            "Covered once by TC01. Every other case asserts behaviour"],
           ["Theme switching", "Cosmetic. No functional risk"],
           ["Responsive layout", "Cosmetic. Better served by a visual tool"],
           ["Variant dimensions per category",
            "A data assertion dressed as a test"],
           ["Visual regression", "Add once the functional suite is green"],
           ["Accessibility audit", "Separate discipline, separate tooling"],
           ["Non-Chromium browsers", "Add after the suite is stable"]])

    ws.column_dimensions["A"].width = 32
    ws.column_dimensions["B"].width = 74
    ws.column_dimensions["C"].width = 14
    for row in ws.iter_rows():
        for cell in row:
            if cell.alignment.wrap_text is not True:
                cell.alignment = Alignment(vertical="top", wrap_text=True)


def write_summary(ws):
    ws.append(["Coverage summary"])
    ws["A1"].font = Font(bold=True, size=14, color="1F3864")
    ws.append([])
    ws.append(["Working set", len(CASES)])
    ws.append(["Automated", sum(1 for c in CASES if c[0] in AUTOMATED)])
    ws.append(["Future scope", len(FUTURE)])
    ws.append(["Total written up", len(CASES) + len(FUTURE)])
    for row in range(3, 7):
        ws.cell(row=row, column=1).font = Font(bold=True)
        ws.cell(row=row, column=2).font = Font(bold=True)
    ws.append([])
    ws.append(["Everything below counts the working set only."])
    ws[ws.max_row][0].font = Font(italic=True, color="666666")
    ws.append([])

    def counts(title, index, order):
        ws.append([title, "Cases"])
        for cell in ws[ws.max_row]:
            cell.font = Font(bold=True)
            cell.fill = PatternFill("solid", fgColor="E8EDF5")
        for key in order:
            ws.append([key, sum(1 for c in CASES if c[index] == key)])
        ws.append(["Total", len(CASES)])
        ws[ws.max_row][0].font = Font(bold=True)
        ws[ws.max_row][1].font = Font(bold=True)
        ws.append([])

    counts("By suite", 3, ["Smoke", "Sanity", "Regression"])
    counts("By priority", 5, ["P1", "P2", "P3"])
    counts("By scope", 4, ["Feature", "End-to-End", "Negative"])

    areas = []
    for case in CASES:
        if case[2] not in areas:
            areas.append(case[2])
    counts("By feature area", 2, areas)

    ws.column_dimensions["A"].width = 26
    ws.column_dimensions["B"].width = 10


def main():
    book = Workbook()
    write_cases(book.active)
    book.active.title = "Test Cases"
    write_reference(book.create_sheet("Test Data"))
    write_summary(book.create_sheet("Summary"))
    book.save(OUT)
    print(f"wrote {OUT}: {len(CASES)} working, {len(FUTURE)} future scope")


if __name__ == "__main__":
    main()
