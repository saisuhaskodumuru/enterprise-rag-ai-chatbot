"""Seeded support documents.

Every document is synthetic, written for this demo. This is not Verizon
production data and contains no real customer data, no real account
numbers, and no real customer names.
"""

SEED_DOCUMENTS = [
    {
        "id": "DOC-BILLING-001",
        "title": "Understanding your monthly bill and payment methods",
        "category": "billing",
        "text": (
            "Your monthly bill is generated on the first day of each billing "
            "cycle and covers the previous month of service. The bill lists "
            "your plan charges, any add-on services, taxes, and one-time "
            "fees such as device instalments. You can pay by credit card, "
            "debit card, or bank transfer through the billing portal, or by "
            "setting up autopay so the amount is charged automatically on "
            "the due date. If a payment fails, we retry the card after "
            "three days and send an email reminder; service is not "
            "suspended until the payment is 30 days overdue. To change your "
            "payment method, open Billing, then Payment Methods, and add "
            "the new card before removing the old one, so autopay is never "
            "interrupted. A late fee of five dollars applies only after the "
            "account is 15 days past due. You can download past invoices as "
            "PDF files from Billing History for up to 24 months."
        ),
    },
    {
        "id": "DOC-ACCOUNT-001",
        "title": "Resetting your password and recovering your account",
        "category": "account",
        "text": (
            "If you forgot your password, use the Forgot Password link on "
            "the sign-in page. We send a one-time reset code to the email "
            "address or phone number on your account; the code expires "
            "after 15 minutes. Choose a new password of at least 12 "
            "characters with a mix of letters, numbers, and symbols, and do "
            "not reuse a password from another service. If you no longer "
            "have access to the email or phone on file, you can verify your "
            "identity with the last four digits of the payment card on the "
            "account and the answer to your security question. Two-factor "
            "authentication can be turned on in Account Settings under "
            "Security, using an authenticator app or text messages. After "
            "five failed sign-in attempts the account is locked for 30 "
            "minutes. To update the email address on your account, sign in "
            "first, then go to Profile and confirm the change through a "
            "verification link sent to the new address."
        ),
    },
    {
        "id": "DOC-ORDERS-001",
        "title": "Tracking an order and delivery times",
        "category": "orders",
        "text": (
            "You can track an order from Orders in your account, where each "
            "order shows its status: processing, shipped, out for delivery, "
            "or delivered. Standard shipping takes three to five business "
            "days, express shipping takes one to two business days, and "
            "same-day delivery is available in selected cities for orders "
            "placed before noon. Once an order ships, a tracking number is "
            "sent by email and text, and the carrier page shows the latest "
            "scan. If the tracking page has not updated for more than 48 "
            "hours, contact support with the order number and we will open "
            "a carrier investigation. Deliveries require a signature only "
            "for orders over 500 dollars. You can change the delivery "
            "address only while the order is still in processing; after it "
            "ships, the address can only be changed through the carrier."
        ),
    },
    {
        "id": "DOC-RETURNS-001",
        "title": "Returns and refunds policy",
        "category": "returns",
        "text": (
            "Most items can be returned within 30 days of delivery for a "
            "full refund to the original payment method. The item must be "
            "in its original condition with all accessories and packaging. "
            "To start a return, open Orders, choose the item, and select "
            "Return; a prepaid return label is emailed to you. Refunds are "
            "issued within five to seven business days after the returned "
            "item arrives at our warehouse, and the money appears on your "
            "statement within a further three to five business days "
            "depending on your bank. Items bought on sale can be returned "
            "for a refund in the same way, but clearance items are final "
            "sale and cannot be returned. If an item arrives damaged or "
            "defective, report it within 14 days and we will send a "
            "replacement at no cost, without waiting for the return. "
            "Restocking fees do not apply to any return."
        ),
    },
    {
        "id": "DOC-SUPPORT-001",
        "title": "Setting up your router and fixing connection problems",
        "category": "product support",
        "text": (
            "To set up your router, plug it into power and connect it to "
            "the modem with the supplied ethernet cable, then wait about "
            "two minutes for the status light to turn solid white. Open the "
            "setup app, scan the QR code on the base of the router, and "
            "follow the steps to name your Wi-Fi network and set a "
            "password. If the internet light is red, restart the modem "
            "first, wait 60 seconds, then restart the router. If the "
            "connection drops often, move the router to a central, open "
            "location away from thick walls and metal objects, and keep it "
            "away from microwaves and baby monitors that interfere on the "
            "2.4 GHz band. A factory reset is done by holding the reset "
            "button for 10 seconds; this erases your Wi-Fi name and "
            "password, so you will need to set the router up again. "
            "Firmware updates are installed automatically overnight."
        ),
    },
    {
        "id": "DOC-WARRANTY-001",
        "title": "Device warranty and repair options",
        "category": "warranty",
        "text": (
            "Every device includes a one-year limited warranty covering "
            "manufacturing defects in materials and workmanship, starting "
            "on the delivery date. The warranty does not cover accidental "
            "damage such as cracked screens or water damage, unless you "
            "bought the optional protection plan, which covers accidental "
            "damage with a 29 dollar service fee per claim. To make a "
            "warranty claim, open Support, choose the device, and describe "
            "the problem; we will first run remote diagnostics, and if the "
            "device cannot be fixed remotely we will arrange a repair or a "
            "replacement. Mail-in repairs take five to seven business days "
            "including shipping, and in-store repairs are usually finished "
            "the same day. A replacement device under warranty is a "
            "refurbished unit of the same model. Keep your proof of "
            "purchase, because the warranty start date is based on the "
            "delivery date on the order."
        ),
    },
    {
        "id": "DOC-PLANS-001",
        "title": "Changing, upgrading, or cancelling your plan",
        "category": "plans",
        "text": (
            "You can change your plan at any time from Plans in your "
            "account. Upgrades take effect immediately, and the extra "
            "charge is prorated for the rest of the billing cycle, so you "
            "only pay for the days you use the higher plan. Downgrades take "
            "effect at the start of the next billing cycle, so you keep the "
            "current plan until then. Cancelling a plan stops service at "
            "the end of the current billing cycle, and no refund is given "
            "for the unused part of a monthly plan, except where the law "
            "requires one. If you are on a contract, an early cancellation "
            "fee may apply; the fee is shown on the cancellation screen "
            "before you confirm. Your phone number can be kept when you "
            "cancel, and you have 60 days to port it to another provider "
            "before it is released."
        ),
    },
    {
        "id": "DOC-SECURITY-001",
        "title": "Keeping your account secure and reporting suspicious activity",
        "category": "security",
        "text": (
            "We will never ask for your password, one-time code, or full "
            "payment card number by email, text, or phone. If you receive a "
            "message asking for those details, do not reply or click its "
            "links; forward the message to the security team and delete it. "
            "Check the recent sign-in activity in Account Settings under "
            "Security to see the devices and locations that accessed your "
            "account, and sign out any device you do not recognise. If you "
            "think someone has accessed your account, change your password "
            "immediately, turn on two-factor authentication, and contact "
            "support so we can review recent changes to your plan, payment "
            "method, and orders. We monitor accounts for unusual sign-in "
            "patterns, such as sign-ins from a new country, and we send an "
            "alert when one is detected."
        ),
    },
]
