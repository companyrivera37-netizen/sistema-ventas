(function () {
  const btn = document.getElementById("scrape-btn");
  if (!btn) return;

  const urlInput = document.getElementById("scrape-url");
  const estado = document.getElementById("scrape-estado");
  const imagenesBox = document.getElementById("scrape-imagenes");

  const nombreInput = document.getElementById("nombre");
  const marcaInput = document.getElementById("marca");
  const descripcionInput = document.getElementById("descripcion");
  const precioVentaInput = document.getElementById("precio_venta");
  const precioReferenciaInput = document.getElementById("precio_referencia");
  const urlReferenciaInput = document.getElementById("url_referencia");
  const origenInput = document.getElementById("origen");

  btn.addEventListener("click", async () => {
    const url = urlInput.value.trim();
    if (!url) {
      estado.textContent = "Pega primero el link del producto.";
      estado.className = "hint texto-negativo";
      return;
    }

    btn.disabled = true;
    estado.textContent = "Buscando información del producto...";
    estado.className = "hint";
    imagenesBox.hidden = true;
    imagenesBox.innerHTML = "";

    try {
      const resp = await fetch("/productos/scrape-link", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const data = await resp.json();

      if (!resp.ok || !data.ok) {
        estado.textContent = data.error || "No se pudo traer la información de ese link.";
        estado.className = "hint texto-negativo";
        return;
      }

      const datos = data.datos;
      nombreInput.value = datos.nombre || "";
      marcaInput.value = datos.marca || "";
      descripcionInput.value = datos.descripcion || "";
      if (datos.precio_referencia) {
        precioVentaInput.value = datos.precio_referencia;
        precioReferenciaInput.value = datos.precio_referencia;
      }
      urlReferenciaInput.value = url;
      origenInput.value = "scrapeado";

      (datos.imagenes || []).forEach((imgUrl, i) => {
        const label = document.createElement("label");
        label.innerHTML = `
          <input type="checkbox" name="imagen_scrapeada" value="${imgUrl}" ${i === 0 ? "checked" : ""}>
          <img src="${imgUrl}" alt="Imagen del producto">
        `;
        imagenesBox.appendChild(label);
      });
      if ((datos.imagenes || []).length) {
        imagenesBox.hidden = false;
      }

      estado.textContent = "Datos traídos. Revisa/ajusta el costo y el precio de venta antes de guardar.";
      estado.className = "hint texto-positivo";
    } catch (error) {
      estado.textContent = "Error de conexión al intentar traer los datos.";
      estado.className = "hint texto-negativo";
    } finally {
      btn.disabled = false;
    }
  });
})();
