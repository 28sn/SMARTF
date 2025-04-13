from flask import Flask, render_template, jsonify, request, redirect, url_for
from datetime import datetime
from collections import OrderedDict
import threading
import requests
import time
import os
import scan  # استيراد ملف scan.py
from scan import get_product_info  # استيراد دالة get_product_info من scan.py
from flask import jsonify
import qrcode
from flask import send_file
from io import BytesIO


app = Flask(__name__)

PRODUCT_FILE = "product_info.txt"
RECIPE_FILE = "recipes.txt"
SHOPPING_FILE = "shopping_cart.txt"








# دالة لقراءة المنتجات من ملف النص
def read_products():
    if not os.path.exists(PRODUCT_FILE):
        return []
    
    with open(PRODUCT_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()

    blocks = content.split("==================================================")
    products = []
    
    for block in blocks:
        lines = block.strip().splitlines()
        data = {}
        
        for line in lines:
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip().lower()
                val = val.strip()

                if key == "product name":
                    data["name"] = val
                elif key == "brand":
                    data["brand"] = val
                elif key == "ingredients":
                    data["ingredients"] = val
                elif key == "energy":
                    data["energy"] = val.replace("kcal", "").strip()
                elif key == "expiration date":
                    # عدم التعديل على تاريخ الانتهاء
                    data["expires"] = val  # اخذ التاريخ كما هو من الملف
                elif key == "barcode":
                    data["barcode"] = val

        if data:
            products.append(data)
    
    return products

@app.route("/api/qr_shopping")
def generate_shopping_qr():
    cart = read_cart()
    if not cart:
        return jsonify({"message": "🧺 السلة فارغة"})

    content = "\n".join([f"- {item['name']} × {item['quantity']}" for item in cart])

    qr = qrcode.make(content)
    img_io = BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')
@app.route("/api/products")
def get_all_products():
    products = read_products()  # قراءة المنتجات من ملف النص
    return jsonify(products)  # إرسال البيانات في شكل JSON

@app.route("/delete_product", methods=["POST"])
def delete_product():
    product_name = request.form["product_name"].strip().lower()
    products = read_products()  # قراءة جميع المنتجات من الملف
    updated_products = [p for p in products if p['name'].lower() != product_name]  # إزالة المنتج المحدد

    # إعادة كتابة الملف بعد الحذف
    with open(PRODUCT_FILE, "w", encoding="utf-8") as f:
        for product in updated_products:
            f.write(f"Product Information:\n")
            f.write(f"Product Name: {product['name']}\n")
            f.write(f"Brand: {product['brand']}\n")
            f.write(f"Ingredients: {product['ingredients']}\n")
            f.write(f"Energy: {product['energy']}\n")
            f.write(f"Expiration Date: {product['expires']}\n")
            f.write(f"Barcode: {product['barcode']}\n")
            f.write("="*50 + "\n")

    return redirect(url_for("inventory"))  # إعادة التوجيه إلى صفحة المخزون بعد الحذف


# دالة لقراءة الوصفات من ملف النص
def read_recipes():
    if not os.path.exists(RECIPE_FILE):
        return []
    with open(RECIPE_FILE, "r") as f:
        lines = f.read().strip().splitlines()
    recipes = []
    current = {}
    for line in lines:
        if line.startswith("name:"):
            if current:
                recipes.append(current)
            current = {"name": line.replace("name:", "").strip()}
        elif line.startswith("ingredients:"):
            ing = line.replace("ingredients:", "").strip()
            current["ingredients"] = [i.strip().lower() for i in ing.split(",")]
    if current:
        recipes.append(current)
    return recipes

# دالة لقراءة سلة التسوق من ملف النص
def read_cart():
    if not os.path.exists(SHOPPING_FILE):
        return []
    with open(SHOPPING_FILE, "r") as f:
        lines = f.read().strip().splitlines()
    cart = {}
    for line in lines:
        item = line.strip().lower()
        if item:
            cart[item] = cart.get(item, 0) + 1
    return [{"name": name, "quantity": qty} for name, qty in cart.items()]

# دالة لإضافة عنصر إلى سلة التسوق
def add_to_cart(items):
    with open(SHOPPING_FILE, "a") as f:
        for item in items:
            f.write(item.strip().lower() + "\n")

@app.route("/")
def index():
    return render_template("index.html")
@app.route("/alerts")
def alerts():
    today = datetime.today()  # التاريخ الحالي
    products = read_products()  # قراءة جميع المنتجات من ملف النص
    alerts = {"expired": [], "ok": [], "soon": []}  # تصنيف التنبيهات إلى ثلاث فئات

    for product in products:
        if "expires" in product and product["expires"]:
            try:
                # تحويل تاريخ الانتهاء إلى كائن datetime
                exp = datetime.strptime(product["expires"], "%Y-%m-%d")
                diff = (exp - today).days  # الفرق بين تاريخ اليوم وتاريخ الانتهاء

                # تصنيف المنتج بناءً على تاريخ الانتهاء
                if diff < 0:
                    product["status"] = "expired"  # المنتج انتهت صلاحيتها
                    alerts["expired"].append(product)
                elif diff <= 30:
                    product["status"] = "soon"  # المنتج سينتهي قريبًا
                    alerts["soon"].append(product)
                else:
                    product["status"] = "ok"  # المنتج صالح
                    alerts["ok"].append(product)
            except Exception as e:
                print(f"Error processing expiration date for product {product['name']}: {e}")
                continue  # إذا فشل في معالجة تاريخ الانتهاء، يتم تجاهل هذا المنتج

    # تمرير المتغير alerts إلى القالب
    return render_template("alerts.html", alerts=alerts)



@app.route("/inventory")
def inventory():
    products = read_products()  # قراءة المنتجات من ملف النص
    return render_template("inventory.html", products=products)

@app.route("/recipes")
def recipes():
    return render_template("recipes.html")

@app.route("/shopping")
def shopping():
    cart = read_cart()
    return render_template("shopping.html", cart=cart)


@app.route("/products")
def get_products():
    return jsonify(read_products())

@app.route("/settings")
def settings():
    return render_template("settings.html")

@app.route("/healthy_tips")
def healthy_tips():
    return render_template("healthy_tips.html")
@app.route("/cleaning")
def cleaning_reminder():
    return render_template("cleaning_reminder.html")

@app.route("/settings/allergy")
def allergy_settings():
    return render_template("settings/allergy.html")
@app.route("/add_product_choice")
def add_product_choice():
    return render_template("add_product_choice.html")


@app.route("/api/old_count")
def old_product_count():
    from datetime import datetime
    import os

    count = 0
    if os.path.exists("product_info.txt"):
        with open("product_info.txt", "r", encoding="utf-8") as f:
            content = f.read().strip().split("=" * 50)
            for block in content:
                lines = block.strip().splitlines()
                for line in lines:
                    if "Expiration Date" in line:
                        try:
                            date_str = line.split(":", 1)[1].strip()
                            exp = datetime.strptime(date_str, "%Y-%m-%d")
                            if exp < datetime.today():
                                count += 1
                        except:
                            continue
    return {"count": count}

@app.route("/api/alerts")
def get_alerts():
    today = datetime.today()  # التاريخ الحالي
    products = read_products()  # قراءة المنتجات من ملف النص
    alerts = {"expired": [], "ok": [], "soon": []}  # تصنيف التنبيهات إلى ثلاث فئات
    
    for product in products:
        if "expires" in product and product["expires"]:
            try:
                # تحويل تاريخ الانتهاء إلى كائن datetime
                exp = datetime.strptime(product["expires"], "%Y-%m-%d")
                diff = (exp - today).days  # الفرق بين تاريخ اليوم وتاريخ الانتهاء
                
                # تصنيف المنتج بناءً على تاريخ الانتهاء
                if diff < 0:
                    product["status"] = "expired"  # المنتج انتهت صلاحيتها
                    alerts["expired"].append(product)
                elif diff <= 30:
                    product["status"] = "soon"  # المنتج سينتهي قريبًا
                    alerts["soon"].append(product)
                else:
                    product["status"] = "ok"  # المنتج صالح
                    alerts["ok"].append(product)
            except Exception as e:
                print(f"Error processing expiration date for product {product['name']}: {e}")
                continue  # إذا فشل في معالجة تاريخ الانتهاء، يتم تجاهل هذا المنتج

    return jsonify(alerts)  # إرجاع البيانات على شكل JSON

@app.route("/api/shopping")
def get_shopping_cart():
    return jsonify(read_cart())

@app.route("/api/shopping/add", methods=["POST"])
def add_shopping_items():
    data = request.json
    items = data.get("items", [])
    add_to_cart(items)
    return jsonify({"status": "success", "added": items})

@app.route("/api/shopping/remove", methods=["POST"])
def remove_item():
    data = request.json
    item_to_remove = data.get("item", "").strip().lower()
@app.route("/scan_web")
def scan_web():
    return render_template("mobile_scan.html")
@app.route("/api/auto_add_product")
def auto_add_product():
    barcode = request.args.get("barcode", "").strip()
    if not barcode:
        return jsonify({"success": False, "message": "الباركود غير موجود."})

    product_info = get_product_info(barcode)
    if not product_info:
        return jsonify({"success": False, "message": "لم يتم العثور على المنتج."})

    # حفظ المنتج في الملف بدون تاريخ انتهاء (سيُدخل لاحقًا)
    with open("product_info.txt", "a", encoding="utf-8") as f:
        f.write(f"Product Information:\n")
        f.write(f"Product Name: {product_info.get('product_name', 'Not available')}\n")
        f.write(f"Brand: {product_info.get('brands', 'Not available')}\n")
        f.write(f"Ingredients: {product_info.get('ingredients_text', 'Not available')}\n")
        f.write(f"Energy: {product_info.get('nutriments', {}).get('energy-kcal', 'Not available')} kcal\n")
        f.write(f"Expiration Date: \n")  # يكتب لاحقًا
        f.write(f"Barcode: {barcode}\n")
        f.write("="*50 + "\n")

    return jsonify({"success": True})
@app.route("/scan_mobile_full")
def scan_mobile_full():
    return render_template("mobile_scan_full.html")
    if not os.path.exists(SHOPPING_FILE):
        return jsonify({"status": "error", "message": "file not found"})

    with open(SHOPPING_FILE, "r") as f:
        items = f.read().splitlines()

    removed = False
    new_items = []
    for i in items:
        if i.strip().lower() == item_to_remove and not removed:
            removed = True
            continue
        new_items.append(i)

    with open(SHOPPING_FILE, "w") as f:
        f.write("\n".join(new_items) + "\n")

    return jsonify({"status": "removed" if removed else "not found"})

@app.route("/api/recipes")
def get_local_recipes():
    products = read_products()
    all_ingredients = []
    for p in products:
        if "ingredients" in p and p["ingredients"].lower() != "not available":
            all_ingredients += [i.strip().lower() for i in p["ingredients"].split(",")]
    available = set(all_ingredients)
    suggestions = []
    for recipe in read_recipes():
        needed = set(recipe["ingredients"])
        missing = list(needed - available)
        match_level = len(needed) - len(missing)
        suggestions.append({
            "name": recipe["name"],
            "available": list(needed & available),
            "missing": missing,
            "match_percent": int((match_level / len(needed)) * 100)
        })
    suggestions.sort(key=lambda x: -x["match_percent"])
    return jsonify(suggestions)

@app.route("/api/recipes/online")
def get_online_recipes():
    products = read_products()
    all_ingredients = []
    for p in products:
        if "ingredients" in p and p["ingredients"].lower() != "not available":
            all_ingredients += [i.strip().lower() for i in p["ingredients"].split(",")]
    available = set(all_ingredients)
    category_url = "https://www.themealdb.com/api/json/v1/1/filter.php?c=Beef"
    response = requests.get(category_url)
    if response.status_code != 200:
        return jsonify([]) 
    meals = response.json().get("meals", [])[:10]
    suggestions = []
    for meal in meals:
        detail_res = requests.get(f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={meal['idMeal']}")
        meal_data = detail_res.json().get("meals", [])[0]
        ingredients = []
        for i in range(1, 21):
            ing = meal_data.get(f"strIngredient{i}")
            if ing and ing.strip():
                ingredients.append(ing.strip().lower())
        match = list(set(ingredients) & available)
        missing = list(set(ingredients) - available)
        if match:
            suggestions.append({
                "name": meal_data["strMeal"],
                "thumbnail": meal_data["strMealThumb"],
                "instructions": meal_data["strInstructions"],
                "source": meal_data.get("strSource") or f"https://www.themealdb.com/meal/{meal['idMeal']}",
                "available": match,
                "missing": missing
            })
    return jsonify(suggestions)

# مسار لعرض نموذج إضافة منتج
@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    if request.method == "POST":
        # الحصول على بيانات المنتج من النموذج
        product_name = request.form["productName"]
        brand = request.form["brand"]
        ingredients = request.form["ingredients"]
        energy = request.form["energy"]
        expiration_date = request.form["expirationDate"]
        barcode = request.form["barcode"]

        # التحقق من وجود تاريخ الانتهاء وإذا كان فارغًا
        if not expiration_date:
            expiration_date = "غير متوفر"  # يمكنك استخدام "غير متوفر" بدلاً من تاريخ افتراضي

        # حفظ المنتج في ملف النص
        with open(PRODUCT_FILE, "a", encoding="utf-8") as file:
            file.write(f"Product Information:\n")
            file.write(f"Product Name: {product_name}\n")
            file.write(f"Brand: {brand}\n")
            file.write(f"Ingredients: {ingredients}\n")
            file.write(f"Energy: {energy}\n")
            file.write(f"Expiration Date: {expiration_date}\n")
            file.write(f"Barcode: {barcode}\n")
            file.write("="*50 + "\n")

        return redirect(url_for("inventory"))  # إعادة التوجيه إلى صفحة المخزون بعد إضافة المنتج

    return render_template("add_product.html")



@app.route("/enter_expiration_date")
def enter_expiration_date():
    barcode = request.args.get('barcode')
    return render_template("enter_expiration_date.html", barcode=barcode)

@app.route("/save_product_expiration", methods=["POST"])
def save_product_expiration():
    barcode = request.form["barcode"]
    expiration_date = request.form["expirationDate"]

    # التأكد من أن تاريخ الانتهاء ليس فارغًا
    if not expiration_date:
        return "تاريخ الانتهاء مطلوب ولا يمكن أن يكون فارغًا."

    # الحصول على معلومات المنتج عبر الباركود
    product_info = get_product_info(barcode)  # استرجاع معلومات المنتج عبر الباركود
    if product_info:
        product_info["expiration_date"] = expiration_date

        # حفظ التفاصيل في ملف نصي
        with open(PRODUCT_FILE, "a", encoding="utf-8") as f:
            f.write(f"Product Information:\n")
            f.write(f"Product Name: {product_info.get('product_name', 'Not available')}\n")
            f.write(f"Brand: {product_info.get('brands', 'Not available')}\n")
            f.write(f"Ingredients: {product_info.get('ingredients_text', 'Not available')}\n")
            f.write(f"Energy: {product_info.get('nutriments', {}).get('energy-kcal', 'Not available')} kcal\n")
            f.write(f"Expiration Date: {expiration_date}\n")
            f.write(f"Barcode: {barcode}\n")
            f.write("="*50 + "\n")

        return redirect(url_for("inventory"))  # إعادة التوجيه إلى صفحة المخزون بعد الحفظ
    else:
        # في حالة عدم العثور على المنتج
        return render_template("product_not_found.html", barcode=barcode, message="المنتج غير موجود أو لم يتم التعرف عليه.")

# مسار لبدء المسح وإدخال المنتجات
@app.route("/start_scan")
def start_scan():
    result = scan.start_scan()  # استدعاء دالة المسح من scan.py
    return result  # إرجاع النتيجة للمستخدم

if __name__ == "__main__":
    app.run(debug=True)
