
import uuid

# 1. DUMMY ORDER DATA

orders = {
    "ORD101": {
        "customer_name": "Rahul",
        "item_id": "SHOE101",
        "item_name": "Shoes",
        "amount": 2000,
        "email": "rahul@example.com",
        "exchange_eligible": True,
        "payment_method": "UPI"
    },

    "ORD102": {
        "customer_name": "Priya",
        "item_id": "WATCH101",
        "item_name": "Watch",
        "amount": 3500,
        "email": "priya@example.com",
        "exchange_eligible": True,
        "payment_method": "Card"
    },

    "ORD103": {
        "customer_name": "Aman",
        "item_id": "HEAD101",
        "item_name": "Headphones",
        "amount": 1500,
        "email": "aman@example.com",
        "exchange_eligible": False,
        "payment_method": "UPI"
    }
}


# 2. DUMMY INVENTORY DATA

inventory = {
    "SHOE101": 0,
    "WATCH101": 5,
    "HEAD101": 3
}


# 3. TRANSACTION STORAGE

refunds = {}
exchanges = {}


# 4. ORDER LOOKUP TOOL

def lookup_order(order_id):

    if order_id not in orders:
        return {
            "success": False,
            "error": "Order not found"
        }

    return {
        "success": True,
        "order_id": order_id,
        **orders[order_id]
    }


# 5. INVENTORY CHECK TOOL

def check_inventory(item_id):

    if item_id not in inventory:
        return {
            "success": False,
            "error": "Item not found in inventory"
        }

    stock = inventory[item_id]

    return {
        "success": True,
        "item_id": item_id,
        "stock": stock,
        "available": stock > 0
    }


# 6. REFUND PROCESSING TOOL

def process_refund(order_id, reason):

    if order_id not in orders:
        return {
            "success": False,
            "error": "Order not found"
        }

    if order_id in refunds or order_id in exchanges:
        return {
            "success": False,
            "error": "Order already resolved"
        }

    order = orders[order_id]

    if order["exchange_eligible"] and inventory.get(order["item_id"], 0) > 0:
        return {
            "success": False,
            "error": "Replacement stock is available. Refund not permitted."
        }

    refund_id = "REF-" + uuid.uuid4().hex[:8].upper()

    refunds[order_id] = {
        "refund_id": refund_id,
        "amount": order["amount"],
        "reason": reason,
        "status": "Refund initiated"
    }

    return {
        "success": True,
        "refund_id": refund_id,
        "order_id": order_id,
        "refund_amount": order["amount"],
        "payment_method": order["payment_method"],
        "status": "Refund initiated"
    }


# 7. EXCHANGE CONFIRMATION TOOL

def confirm_exchange(order_id):

    if order_id not in orders:
        return {
            "success": False,
            "error": "Order not found"
        }

    if order_id in exchanges or order_id in refunds:
        return {
            "success": False,
            "error": "Order already resolved"
        }

    order = orders[order_id]
    item_id = order["item_id"]

    if not order["exchange_eligible"]:
        return {
            "success": False,
            "error": "Order is not eligible for exchange"
        }

    if inventory.get(item_id, 0) <= 0:
        return {
            "success": False,
            "error": "Replacement stock unavailable"
        }

    inventory[item_id] -= 1

    exchange_id = "EXC-" + uuid.uuid4().hex[:8].upper()

    exchanges[order_id] = {
        "exchange_id": exchange_id,
        "status": "Exchange confirmed"
    }

    return {
        "success": True,
        "exchange_id": exchange_id,
        "order_id": order_id,
        "status": "Exchange confirmed"
    }


# 8. CUSTOMER NOTIFICATION TOOL

def send_notification(email, message):

    print("\n========== EMAIL NOTIFICATION ==========")
    print("To:", email)
    print("Message:", message)
    print("Status: Email simulated successfully")
    print("========================================")

    return {
        "success": True,
        "email": email,
        "status": "Notification sent (simulated)"
    }
