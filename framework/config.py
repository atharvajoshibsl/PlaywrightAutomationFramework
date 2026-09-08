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
