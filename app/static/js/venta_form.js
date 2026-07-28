(function () {
  const form = document.getElementById("form-venta");
  if (!form) return;

  // --- Selección de producto (galería) ---
  const galeria = document.getElementById("galeria-productos");
  const productoIdInput = document.getElementById("producto_id");
  const precioInput = document.getElementById("precio_unitario");
  const productoElegido = document.getElementById("producto-elegido");

  function elegirProducto(card) {
    galeria.querySelectorAll(".producto-card").forEach((c) => c.classList.remove("seleccionado"));
    card.classList.add("seleccionado");
    productoIdInput.value = card.dataset.id;
    precioInput.value = card.dataset.precio;
    productoElegido.textContent = "Elegiste: " + card.dataset.nombre;
    productoElegido.className = "hint texto-positivo";
  }

  if (galeria) {
    galeria.querySelectorAll(".producto-card").forEach((card) => {
      card.addEventListener("click", () => elegirProducto(card));
    });
    const prefillId = window.__PRODUCTO_ID_PREFILL__;
    if (prefillId) {
      const card = galeria.querySelector(`.producto-card[data-id="${prefillId}"]`);
      if (card) elegirProducto(card);
    }
  }

  // --- Autocompletado de cliente ---
  const buscarInput = document.getElementById("cliente-buscar");
  const clienteIdInput = document.getElementById("cliente_id");
  const resultados = document.getElementById("cliente-resultados");
  let debounceTimer = null;

  if (buscarInput) {
    buscarInput.addEventListener("input", () => {
      clienteIdInput.value = ""; // si el usuario sigue escribiendo, invalida la seleccion anterior
      clearTimeout(debounceTimer);
      const termino = buscarInput.value.trim();
      if (termino.length < 2) {
        resultados.hidden = true;
        resultados.innerHTML = "";
        return;
      }
      debounceTimer = setTimeout(async () => {
        try {
          const resp = await fetch(`/clientes/api/buscar?q=${encodeURIComponent(termino)}`);
          const clientes = await resp.json();
          resultados.innerHTML = "";
          if (!clientes.length) {
            resultados.hidden = true;
            return;
          }
          clientes.forEach((c) => {
            const item = document.createElement("div");
            item.textContent = `${c.nombres} · ${c.celular}`;
            item.style.cursor = "pointer";
            item.style.padding = "6px 0";
            item.addEventListener("click", () => {
              clienteIdInput.value = c.id;
              buscarInput.value = c.nombres;
              resultados.hidden = true;
            });
            resultados.appendChild(item);
          });
          resultados.hidden = false;
        } catch (error) {
          resultados.hidden = true;
        }
      }, 300);
    });
  }

  // --- Contado / crédito ---
  const camposCredito = document.getElementById("campos-credito");
  form.querySelectorAll('input[name="tipo_venta"]').forEach((radio) => {
    radio.addEventListener("change", () => {
      camposCredito.hidden = radio.value !== "credito" ? true : false;
      if (document.querySelector('input[name="tipo_venta"]:checked').value === "credito") {
        camposCredito.hidden = false;
      } else {
        camposCredito.hidden = true;
      }
    });
  });

  // --- Frecuencia de cobro: mostrar fecha manual solo si aplica ---
  const frecuenciaSelect = document.getElementById("frecuencia_cobro");
  const campoFechaManual = document.getElementById("campo-fecha-manual");
  if (frecuenciaSelect) {
    frecuenciaSelect.addEventListener("change", () => {
      campoFechaManual.hidden = frecuenciaSelect.value !== "manual";
    });
  }

  // --- Validación mínima antes de enviar ---
  form.addEventListener("submit", (evento) => {
    if (!productoIdInput.value) {
      evento.preventDefault();
      alert("Elige un producto de la galería antes de guardar la venta.");
      return;
    }
    if (!clienteIdInput.value) {
      evento.preventDefault();
      alert("Busca y selecciona un cliente de la lista antes de guardar la venta.");
    }
  });
})();
