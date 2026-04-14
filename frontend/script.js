const formBien = document.getElementById("formBien");
const btnCargarBienes = document.getElementById("btnCargarBienes");
const btnImportarExcel = document.getElementById("btnImportarExcel");
const btnDesplazar = document.getElementById("btnDesplazar");
const btnCargarHistorial = document.getElementById("btnCargarHistorial");

const inputCodigo = document.getElementById("codigo_patrimonial");
const inputNombre = document.getElementById("nombre");
const inputDescripcion = document.getElementById("descripcion");
const inputEstado = document.getElementById("estado");
const inputPersonaAsignada = document.getElementById("persona_asignada");

const archivoExcel = document.getElementById("archivoExcel");
const resultadoImportacion = document.getElementById("resultadoImportacion");

const tablaBienes = document.getElementById("tablaBienes");
const tablaHistorial = document.getElementById("tablaHistorial");

const inputNuevaPersona = document.getElementById("nueva_persona");
const inputMotivo = document.getElementById("motivo");

const API_URL = "http://127.0.0.1:5000";

formBien.addEventListener("submit", async function (e) {
    e.preventDefault();

    const datos = {
        codigo_patrimonial: inputCodigo.value.trim(),
        nombre: inputNombre.value.trim(),
        descripcion: inputDescripcion.value.trim(),
        estado: inputEstado.value.trim(),
        persona_asignada: inputPersonaAsignada.value.trim()
    };

    if (
        !datos.codigo_patrimonial ||
        !datos.nombre ||
        !datos.descripcion ||
        !datos.estado ||
        !datos.persona_asignada
    ) {
        alert("Complete todos los campos");
        return;
    }

    try {
        const response = await fetch(`${API_URL}/registrar_bien`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(datos)
        });

        const resultado = await response.json();

        if (resultado.ok) {
            alert(resultado.mensaje);
            formBien.reset();
            inputCodigo.focus();
            cargarBienes();
        } else {
            alert(resultado.mensaje);
        }

    } catch (error) {
        alert("Error al conectar con el backend");
        console.error(error);
    }
});

btnCargarBienes.addEventListener("click", function () {
    cargarBienes();
});

async function cargarBienes() {
    try {
        const response = await fetch(`${API_URL}/bienes`);
        const bienes = await response.json();

        tablaBienes.innerHTML = "";

        bienes.forEach(bien => {
            const fila = document.createElement("tr");

            fila.innerHTML = `
                <td>
                    <input type="checkbox" class="check-bien" value="${bien.id}">
                </td>
                <td>${bien.id}</td>
                <td>${bien.codigo_patrimonial}</td>
                <td>${bien.nombre}</td>
                <td>${bien.descripcion}</td>
                <td>${bien.estado}</td>
                <td>${bien.persona_asignada}</td>
            `;

            tablaBienes.appendChild(fila);
        });

    } catch (error) {
        alert("Error al obtener los bienes");
        console.error(error);
    }
}

btnImportarExcel.addEventListener("click", async function () {
    const archivo = archivoExcel.files[0];

    if (!archivo) {
        alert("Seleccione un archivo Excel");
        return;
    }

    const formData = new FormData();
    formData.append("archivo", archivo);

    try {
        const response = await fetch(`${API_URL}/importar_excel`, {
            method: "POST",
            body: formData
        });

        const resultado = await response.json();

        if (resultado.ok) {
            resultadoImportacion.textContent =
                `Importación completada. Registrados: ${resultado.registrados}, Duplicados: ${resultado.duplicados}, Incompletos: ${resultado.incompletos}`;
            cargarBienes();
        } else {
            resultadoImportacion.textContent = resultado.mensaje;
            alert(resultado.mensaje);
        }

    } catch (error) {
        alert("Error al importar Excel");
        console.error(error);
    }
});

btnDesplazar.addEventListener("click", async function () {
    const checks = document.querySelectorAll(".check-bien:checked");
    const bienesSeleccionados = Array.from(checks).map(check => parseInt(check.value));

    const nueva_persona = inputNuevaPersona.value.trim();
    const motivo = inputMotivo.value.trim();

    if (bienesSeleccionados.length === 0) {
        alert("Seleccione al menos un bien");
        return;
    }

    if (!nueva_persona) {
        alert("Ingrese la nueva persona");
        return;
    }

    if (!motivo) {
        alert("Ingrese el motivo");
        return;
    }

    try {
        const response = await fetch(`${API_URL}/desplazar_bienes`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                bienes_ids: bienesSeleccionados,
                nueva_persona: nueva_persona,
                motivo: motivo
            })
        });

        const resultado = await response.json();

        if (resultado.ok) {
            alert(resultado.mensaje);
            inputNuevaPersona.value = "";
            inputMotivo.value = "";
            cargarBienes();
            cargarHistorial();
        } else {
            alert(resultado.mensaje);
        }

    } catch (error) {
        alert("Error al realizar desplazamiento");
        console.error(error);
    }
});

btnCargarHistorial.addEventListener("click", function () {
    cargarHistorial();
});

async function cargarHistorial() {
    try {
        const response = await fetch(`${API_URL}/historial`);
        const historial = await response.json();

        tablaHistorial.innerHTML = "";

        historial.forEach(item => {
            const fila = document.createElement("tr");

            fila.innerHTML = `
                <td>${item.id}</td>
                <td>${item.codigo_patrimonial}</td>
                <td>${item.nombre_bien}</td>
                <td>${item.persona_anterior}</td>
                <td>${item.persona_nueva}</td>
                <td>${item.motivo}</td>
                <td>${item.fecha}</td>
            `;

            tablaHistorial.appendChild(fila);
        });

    } catch (error) {
        alert("Error al obtener historial");
        console.error(error);
    }
}

const btnPDF = document.getElementById("btnPDF");

btnPDF.addEventListener("click", function () {
    window.open("http://127.0.0.1:5000/reporte_bienes_pdf", "_blank");
});