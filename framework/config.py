"""What the application is expected to contain.

These are the suite's oracle: the answer to "what is correct" lives here, in
one readable place, rather than being scattered through assertions. When the
shop adds a category, one line changes here and every test that cares fails
until it does.

The target URL is deliberately absent - that is environment, not expectation,
and pytest.ini owns it so it can be overridden per run.
"""

# The shop seeds this many products, and every reset restores the count.
EXPECTED_PRODUCT_COUNT = 16

# Below this window width the stylesheet hides the header tagline on purpose,
# so it cannot collide with the search box.
TAGLINE_BREAKPOINT = 1180

# "All" is a chip too, not just the four real categories.
CATEGORIES = ["All", "Apparel", "Electronics", "Footwear", "Home & Kitchen"]

# What each category chip should list, keyed by the slug its data-testid uses.
# A card carries no category of its own, so naming the products is the only way
# to prove a filter kept exactly the right ones and dropped the rest.
#
# The order matters: Relevance sorts by insertion order, so this is also the
# order the cards appear in until another sort is chosen.
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
