// URL base de tu API Flask
const API_URL = 'http://localhost:8000';

// Elementos del DOM
const productsTable = document.getElementById('products-table').querySelector('tbody');
const salesTable = document.getElementById('sales-table').querySelector('tbody');
const addProductForm = document.getElementById('add-product-form');
const saleForm = document.getElementById('sale-form');
const productSelect = document.getElementById('product_id');
const productAlert = document.getElementById('product-alert');
const saleAlert = document.getElementById('sale-alert');

// Variables de paginación
let currentPage = 1;
let totalPages = 1;
let editingProductId = null;

// Elementos de paginación
const paginationContainer = document.createElement('div');
paginationContainer.className = 'pagination';
document.querySelector('.card').appendChild(paginationContainer);

// Cargar datos al iniciar
document.addEventListener('DOMContentLoaded', () => {
    loadProducts();
    loadSales();
    fillProductSelect();
});

// Mostrar alertas
function showAlert(element, message, type = 'success') {
    element.textContent = message;
    element.className = `alert alert-${type}`;
    element.style.display = 'block';
    setTimeout(() => {
        element.style.display = 'none';
    }, 2500);
}

// Cargar productos con paginación
async function loadProducts(page = 1) {
    try {
        const response = await fetch(`${API_URL}/products?page=${page}`);
        if (!response.ok) throw new Error(`Error HTTP: ${response.status}`);
        const data = await response.json();

        currentPage = data.current_page;
        totalPages = data.pages;

        productsTable.innerHTML = '';
        if (data.products && data.products.length > 0) {
            data.products.forEach(product => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${product.id}</td>
                    <td>${product.name}</td>
                    <td>$${product.price}</td>
                    <td>${product.quantity}</td>
                    <td class="actions">
                        <button onclick="editProduct(${product.id})" class="btn btn-primary">✏️ Editar</button>
                        <button onclick="deleteProduct(${product.id})" class="btn btn-danger">🗑️ Eliminar</button>
                    </td>
                `;
                productsTable.appendChild(row);
            });
            updatePaginationControls();
        } else {
            productsTable.innerHTML = '<tr><td colspan="5">No hay productos registrados</td></tr>';
        }
    } catch (error) {
        showAlert(productAlert, `Error al cargar productos: ${error.message}`, 'error');
    }
}

// Actualizar controles de paginación
function updatePaginationControls() {
    paginationContainer.innerHTML = '';

    if (currentPage > 1) {
        const prevBtn = document.createElement('button');
        prevBtn.textContent = '← Anterior';
        prevBtn.className = 'btn btn-primary';
        prevBtn.addEventListener('click', () => loadProducts(currentPage - 1));
        paginationContainer.appendChild(prevBtn);
    }

    const pageInfo = document.createElement('span');
    pageInfo.textContent = ` Página ${currentPage} de ${totalPages} `;
    pageInfo.style.margin = '0 10px';
    paginationContainer.appendChild(pageInfo);

    if (currentPage < totalPages) {
        const nextBtn = document.createElement('button');
        nextBtn.textContent = 'Siguiente →';
        nextBtn.className = 'btn btn-primary';
        nextBtn.addEventListener('click', () => loadProducts(currentPage + 1));
        paginationContainer.appendChild(nextBtn);
    }
}

// Cargar productos en el select de ventas
async function fillProductSelect() {
    try {
        const response = await fetch(`${API_URL}/products`);
        const data = await response.json();
        productSelect.innerHTML = '<option disabled selected>Seleccione un producto</option>';
        data.products.forEach(p => {
            const option = document.createElement('option');
            option.value = p.id;
            option.textContent = p.name;
            productSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error al cargar select de productos:', error);
    }
}

// AGREGAR O ACTUALIZAR PRODUCTO
addProductForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = addProductForm.name.value.trim();
    const price = parseFloat(addProductForm.price.value);
    const quantity = parseInt(addProductForm.quantity.value);

    if (!name || isNaN(price) || isNaN(quantity)) {
        showAlert(productAlert, 'Datos inválidos', 'error');
        return;
    }

    try {
        const url = editingProductId ? `${API_URL}/products/${editingProductId}` : `${API_URL}/products`;
        const method = editingProductId ? 'PUT' : 'POST';
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, price, quantity })
        });

        if (!response.ok) throw new Error('Error al guardar producto');

        showAlert(productAlert, editingProductId ? 'Producto actualizado' : 'Producto agregado', 'success');
        addProductForm.reset();
        editingProductId = null;
        addProductForm.querySelector('button[type="submit"]').textContent = 'Agregar';
        loadProducts(currentPage);
        fillProductSelect();
    } catch (error) {
        showAlert(productAlert, error.message, 'error');
    }
});

// EDITAR PRODUCTO
function editProduct(id) {
    fetch(`${API_URL}/products/${id}`)
        .then(res => res.json())
        .then(product => {
            addProductForm.name.value = product.name;
            addProductForm.price.value = product.price;
            addProductForm.quantity.value = product.quantity;
            editingProductId = id;
            addProductForm.querySelector('button[type="submit"]').textContent = 'Actualizar';
        });
}
window.editProduct = editProduct;

// ELIMINAR PRODUCTO
async function deleteProduct(id) {
    if (confirm('¿Seguro que deseas eliminar este producto?')) {
        try {
            const response = await fetch(`${API_URL}/products/${id}`, { method: 'DELETE' });
            if (!response.ok) throw new Error('No se pudo eliminar el producto');
            showAlert(productAlert, 'Producto eliminado correctamente', 'success');
            loadProducts(currentPage);
            fillProductSelect();
        } catch (error) {
            showAlert(productAlert, error.message, 'error');
        }
    }
}
window.deleteProduct = deleteProduct;

// REGISTRAR VENTA - Opción 1: Cambiar la ruta para que coincida con Flask
saleForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const productId = parseInt(saleForm.product_id.value);
    const quantity = parseInt(saleForm.quantity.value);

    if (!productId || isNaN(quantity) || quantity < 1) {
        showAlert(saleAlert, 'Datos inválidos para la venta', 'error');
        return;
    }

    try {
        // Cambiar la ruta para que coincida con Flask: /products/sell/<id>
        const response = await fetch(`${API_URL}/products/sell/${productId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quantity })  // Solo enviar quantity, el ID va en la URL
        });

        // Verificar si la respuesta es JSON válida
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('El servidor no devolvió una respuesta JSON válida');
        }

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || errorData.message || 'No se pudo registrar la venta');
        }

        const result = await response.json();
        showAlert(saleAlert, 'Venta registrada exitosamente', 'success');
        saleForm.reset();
        loadProducts(currentPage);
        loadSales();
    } catch (error) {
        console.error('Error completo:', error);
        showAlert(saleAlert, error.message, 'error');
    }
});

// CARGAR HISTORIAL DE VENTAS
async function loadSales() {
    try {
        const response = await fetch(`${API_URL}/sales`);
        
        // Verificar si la respuesta es JSON válida
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('El servidor no devolvió una respuesta JSON válida');
        }

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'No se pudo cargar ventas');
        }

        const data = await response.json();
        salesTable.innerHTML = '';
        
        // Verificar si hay ventas
        if (!data.sales || data.sales.length === 0) {
            salesTable.innerHTML = '<tr><td colspan="5">No hay ventas registradas</td></tr>';
            return;
        }

        // Renderizar las ventas con los nombres de campo correctos
        data.sales.forEach(sale => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${sale.id}</td>
                <td>${sale.product_name}</td>
                <td>${sale.quantity}</td>
                <td>$${sale.total_venta}</td>
                <td>${new Date(sale.sale_date).toLocaleString()}</td>
            `;
            salesTable.appendChild(row);
        });

        // Opcional: mostrar información de paginación
        console.log(`Mostrando página ${data.current_page} de ${data.pages} (${data.total} ventas total)`);
        
    } catch (error) {
        console.error('Error completo:', error);
        showAlert(saleAlert, `Error al cargar ventas: ${error.message}`, 'error');
    }
}
