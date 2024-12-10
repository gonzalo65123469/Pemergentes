// Variables globales
let productosVenta = [];
let totalVenta = 0;

// Función para agregar un producto a la tabla
function agregarProducto() {
    const productoSelect = document.getElementById("producto");
    const cantidadInput = document.getElementById("cantidad");

    // Obtén los valores seleccionados
    const idProducto = productoSelect.value;
    const nombreProducto = productoSelect.options[productoSelect.selectedIndex].text;
    const cantidad = parseInt(cantidadInput.value);

    if (cantidad <= 0) {
        alert("La cantidad debe ser mayor a 0");
        return;
    }

    // Precio ficticio para el ejemplo
    const precio = 10; // Cambiar según la lógica del servidor
    const subtotal = precio * cantidad;

    // Agregar el producto al array
    productosVenta.push({ idProducto, nombreProducto, cantidad, precio, subtotal });

    // Actualizar la tabla
    const tablaProductos = document.getElementById("tablaProductos");
    const fila = document.createElement("tr");
    fila.innerHTML = `
        <td>${nombreProducto}</td>
        <td>${cantidad}</td>
        <td>${precio.toFixed(2)}</td>
        <td>${subtotal.toFixed(2)}</td>
    `;
    tablaProductos.appendChild(fila);

    // Actualizar el total
    totalVenta += subtotal;
    document.getElementById("totalVenta").textContent = totalVenta.toFixed(2);

    // Limpiar el formulario
    cantidadInput.value = "";
}

// Función para guardar la venta
function guardarVenta() {
    if (productosVenta.length === 0) {
        alert("Agrega al menos un producto antes de guardar la venta.");
        return;
    }

    const data = {
        productos: productosVenta,
        total: totalVenta,
    };

    fetch("/ventas/registrar", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
    })
    .then((response) => {
        if (response.ok) {
            alert("Venta registrada con éxito");
            // Reinicia el formulario
            productosVenta = [];
            totalVenta = 0;
            document.getElementById("tablaProductos").innerHTML = "";
            document.getElementById("totalVenta").textContent = "0";
        } else {
            alert("Error al registrar la venta");
        }
    })
    .catch((error) => {
        console.error("Error:", error);
        alert("Ocurrió un error al registrar la venta.");
    });
}

// Función para cancelar la venta
function cancelarVenta() {
    if (confirm("¿Estás seguro de que deseas cancelar la venta?")) {
        productosVenta = [];
        totalVenta = 0;
        document.getElementById("tablaProductos").innerHTML = "";
        document.getElementById("totalVenta").textContent = "0";
    }
}

// Event listeners
document.getElementById("agregarProducto").addEventListener("click", agregarProducto);
document.getElementById("guardarVenta").addEventListener("click", guardarVenta);
