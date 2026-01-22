"""Example user inputs for landing page generation."""

from core.schemas import UserInput


# Example 1: Productivity SaaS → template "saas"
EXAMPLE_1 = UserInput(
    product_name="FlowTask",
    target_audience="Freelancers and small teams",
    value_proposition="Save 2 hours a day with AI",
    tone="friendly",
    template_type="agency",
)

# Example 2: B2B Enterprise SaaS → template "saas"
EXAMPLE_2 = UserInput(
    product_name="DataVault",
    target_audience="CIOs and data teams at large enterprises",
    value_proposition="Secure and centralize your sensitive data with GDPR compliance",
    tone="professional",
    additional_context="On-premise solution available, ISO 27001 certified",
    template_type="agency",
)

# Example 3: Bold Consumer App → template "app"
EXAMPLE_3 = UserInput(
    product_name="FitPulse",
    target_audience="Urban millennial athletes",
    value_proposition="The fitness app that adapts to your lifestyle",
    tone="bold",
    additional_context="Gamification, social features, wearables integration",
    template_type="saas",
)

# Example 4: Minimal Developer Tool → template "saas"
EXAMPLE_4 = UserInput(
    product_name="Clipp",
    target_audience="Developers and power users",
    value_proposition="Minimalist and powerful clipboard manager",
    tone="minimal",
    additional_context="Cross-platform, keyboard-first, open source",
    template_type="saas",
)

# Example 5: Creative Agency → template "agency"
EXAMPLE_5 = UserInput(
    product_name="StudioNova",
    target_audience="Startups and scale-ups looking for premium branding",
    value_proposition="Transform your brand into an unforgettable experience",
    tone="professional",
    additional_context="Full-service creative agency, branding, web design, motion",
    template_type="agency",
)

# List of all examples for easy iteration
EXAMPLES = [
    ("FlowTask - Productivity SaaS", EXAMPLE_1),
    ("DataVault - B2B Enterprise", EXAMPLE_2),
    ("FitPulse - Consumer App", EXAMPLE_3),
    ("Clipp - Developer Tool", EXAMPLE_4),
    ("StudioNova - Creative Agency", EXAMPLE_5),
]
