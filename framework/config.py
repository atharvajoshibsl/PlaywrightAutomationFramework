"""Expected application data used as test oracles."""

# Product count after each reset.
EXPECTED_PRODUCT_COUNT = 16

# Tagline hidden below this width (CSS).
TAGLINE_BREAKPOINT = 1180

# "All" is a category chip too.
CATEGORIES = ["All", "Apparel", "Electronics", "Footwear", "Home & Kitchen"]

# Products per category slug. Order matches Relevance sort.
CATEGORY_PRODUCTS = {
    "apparel": [
        "Cotton T-Shirt",
        "Denim Jacket",
        "Hooded Sweatshirt",
        "Formal Shirt",
    ],
    "electronics": [
        "Wireless Mouse",
        "Mechanical Keyboard",
        "Noise Cancelling Headphones",
        "USB-C Hub",
        "Smart Watch",
    ],
    "footwear": [
        "Running Shoes",
        "Leather Loafers",
        "Trail Sandals",
    ],
    "home-kitchen": [
        "Ceramic Mug Set",
        "Cast Iron Skillet",
        "Table Lamp",
        "Storage Baskets",
    ],
}

# The product TC03 opens. Price is read from the card, not fixed here.
DETAIL_PRODUCT = {
    "slug": "mechanical-keyboard",
    "name": "Mechanical Keyboard",
    "brand": "Logiwave",
    "sku": "EL-1002",
    "category": "Electronics",
}

# The product TC04 puts in the cart. Prices are read from the page.
CART_PRODUCT = {
    "slug": "wireless-mouse",
    "name": "Wireless Mouse",
    "variant": "Standard / Default",
}

# Demo accounts, as published on the app's own login page.
DEMO_ACCOUNT = {
    "email": "demo@shop.test",
    "password": "Demo@123",
    "name": "Demo User",
    "wallet": "\u20b95,000",
}

# The account TC05 and TC07 create. Every test starts from a reset, so the
# address is free again each run.
NEW_ACCOUNT = {
    "name": "Fresh Tester",
    "email": "fresh@shop.test",
    "phone": "9876500011",
    "password": "Fresh@123",
}

# One wording for every failed sign-in, so emails cannot be discovered.
LOGIN_REJECTED = "Invalid email or password."
EMAIL_TAKEN = "An account with this email already exists."

# Demo cards, as published on the payment page.
CARDS = {
    "success": "4111 1111 1111 1111",
    "declined": "4000 0000 0000 0002",
    "expired": "4000 0000 0000 0069",
}
CARD_HOLDER = "Demo User"
CARD_EXPIRY = "12/30"
CARD_CVV = "123"

# What the payment page says about each outcome.
CARD_DECLINED = "Your card was declined by the issuing bank."
CARD_EXPIRED = "This card has expired."
PAYMENT_CONFIRMED = "Payment successful. Your order is confirmed."
CART_EMPTY = "Your cart is empty."

SORT_OPTIONS = [
    "Relevance",
    "Price: low to high",
    "Price: high to low",
    "Name: A to Z",
    "Rating",
]

FRAMEWORKS = [
    "Playwright",
    "Selenium",
    "Cypress",
    "Robot Framework",
    "REST API",
]

TAGLINE = "read it correct through automation"
