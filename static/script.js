function fetchProducts() {
  fetch("/products")
    .then(res => res.json())
    .then(data => {
      const table = document.getElementById("productTable");
      table.innerHTML = "<tr><th>الاسم</th><th>العلامة</th><th>الطاقة</th><th>الانتهاء</th></tr>";
      data.forEach(p => {
        table.innerHTML += `<tr>
          <td>${p.name}</td>
          <td>${p.brand}</td>
          <td>${p.energy}</td>
          <td>${p.expires}</td>
        </tr>`;
      });
    });
}

function fetchAlerts() {
  fetch("/api/alerts")
    .then(res => res.json())
    .then(data => {
      const ul = document.getElementById("alerts");
      ul.innerHTML = "";
      data.forEach(p => {
        let color = "green";
        let text = `${p.name} - ينتهي في ${p.expires}`;
        if (p.status === "soon") {
          color = "orange";
          text += ` (ينتهي قريبًا)`;
        }
        if (p.status === "expired") {
          color = "red";
          text += ` (منتهي)`;
        }
        ul.innerHTML += `<li style="color:${color}">${text}</li>`;
      });
    });
}

function fetchRecipes() {
  const ingredients = document.getElementById("ingredients").value;
  fetch(`/api/recipes?ingredients=${ingredients}`)
    .then(res => res.json())
    .then(data => {
      const ul = document.getElementById("recipeSuggestions");
      ul.innerHTML = "";
      data.forEach(recipe => {
        ul.innerHTML += `<li>${recipe.name} - ${recipe.description}</li>`;
      });
    });
}

function fetchShoppingCart() {
  fetch("/api/shopping")
    .then(res => res.json())
    .then(data => {
      const table = document.getElementById("shoppingCartTable");
      table.innerHTML = "<tr><th>المنتج</th><th>العدد</th></tr>";
      data.forEach(item => {
        table.innerHTML += `<tr>
          <td>${item.name}</td>
          <td>${item.quantity}</td>
        </tr>`;
      });
    });
}

if (document.getElementById("productTable")) fetchProducts();
if (document.getElementById("alerts")) fetchAlerts();
if (document.getElementById("shoppingCartTable")) fetchShoppingCart();
