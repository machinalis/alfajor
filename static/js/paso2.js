function costo_de_envio(){
  var loc_elem = null;
  var loc_parent = null;
  var localidad = "";

  if ($("select#id_localidad").length > 0) {
    loc_elem = $("select#id_localidad");
    loc_parent = loc_elem.parent();
    localidad = loc_elem.val();
  }

  var provincia = $("#id_provincia").val();

  if (localidad === "Otra") {
    loc_elem.unbind();
    loc_elem.remove();
    loc_parent.append('<input type="text" '
                      + 'maxlength="256" '
                      + 'name="localidad" '
                      + 'class="required" '
                      + 'id="id_localidad"/>');
    localidad = "";
    _costo_de_envio(provincia, localidad);
  } else {
    _costo_de_envio(provincia, localidad);
  }
}

// ToDo: chenge this to make just one order for all the cities
function _costo_de_envio(prov_arg, loc_arg) {
  if (loc_arg === "NA" || loc_arg === "") {
    loc_arg = null;
  }
  $.ajax({
    url: "/alfajor/ajax/costo-de-envio/",
    data: { provincia: prov_arg, localidad: loc_arg },
    dataType: "json",
    cache: false,
    success: function(res) {
      var c = $("#id_costo_de_envio * span.val").first();
      c.empty();
      c.append(Number(res).toFixed(2).toString());
      _costo_total(); // this is present because of JS async
    }
  });
}

function _costo_total() {
  var costo_pedido = $("#id_costo_pedido * span.val").first().html();
  var costo_de_envio = $("#id_costo_de_envio * span.val").first().html();
  var total = Number(costo_pedido) + Number(costo_de_envio);
  var total_elem = $("#id_costo_total * span.val").first();
  total_elem.empty();
  total_elem.append(total.toFixed(2).toString());

}


function organizar_selects(res) {
  $("label[for='id_localidad']").empty();
  $("label[for='id_localidad']").append("Localidad *");

  var prov = $("#id_provincia").val();
  if (prov === 'C') {
    $("label[for='id_localidad']").empty();
    $("label[for='id_localidad']").append("Barrio *");
  }

  var localidad = "";

  // some local variables
  var elem = null;
  var p = null;
  var loc_elem = null;
  var loc_parent = null;

  if ($("select#id_localidad").length === 0 &&
      res.length > 1) {
    // if it's not a select, then change to it
    // if res.length === 2 is because "NA" and "other" options are available
    // if that's the case, then we leave the input as is

    // sacar el input.
    elem = $("input#id_localidad");
    p = elem.parent();
    elem.remove();
    // agregar select
    p.append("<select id='id_localidad' name='localidad'></select>");

    loc_elem = $("select#id_localidad");
    loc_elem.empty();
    // Add options to the city select
    for (var elem in res) {
      loc_elem.append('<option value="' + res[elem][0] +  '">' +
                      res[elem][1] + '</option>');
    }
    // re bind change event
    loc_elem.change(costo_de_envio);
    // see which is the first city
    localidad = $("#id_localidad > option").first().val();
  } else if ($("select#id_localidad").length > 0 &&
             res.length > 1) {
    // already a select, and more than 2 options
    loc_elem = $("select#id_localidad");
    loc_elem.empty();

    // Add options to city select
    for (var elem in res) {
      loc_elem.append('<option value="' + res[elem][0] +  '">' +
                      res[elem][1] + '</option>');
    }
  } else if ($("input#id_localidad").length > 0 &&
             res.length === 1) {
    // leaves without changes. City inherits province cost if empty
    localidad = "";
  } else if ($("select#id_localidad").length > 0 &&
             res.length === 1) {
    loc_elem = $("select#id_localidad");
    loc_parent = loc_elem.parent();
    loc_elem.unbind();
    loc_elem.remove();
    loc_parent.append('<input type="text" '
                      + 'maxlength="256" '
                      + 'name="localidad" '
                      + 'class="required" '
                      + 'id="id_localidad"/>');
    localidad = "";
  }
  // look for the cost to send to the first city
  _costo_de_envio(prov, localidad);
  _costo_total();
}

$(document).ready(
  function() {

    var provincia = $("select#id_provincia").val();
    $.ajax({
      url: "/alfajor/ajax/localidades/",
      data: "provincia="+provincia,
      dataType: "json",
      cache: false,
      success: organizar_selects
    });

    $("#siguiente").click(
      function() {
        envio=1;
        $(".required").each(
          function() {
	    if($(this).val()=="") envio=0;
	  }
        );
        if (envio == 1) {
          $("form").submit();
        } else {
          alert("Se deben completar todos los campos marcados con (*)");
        }
      }
    );

    $("#id_provincia").change(
      function() {
        var provincia = $(this).val();
	$.ajax({
	  url: "/alfajor/ajax/localidades/",
	  data: "provincia="+provincia,
	  dataType: "json",
	  cache: false,
	  success: organizar_selects
        });
        return false;
      });

     $("#id_localidad").change(costo_de_envio);

});

