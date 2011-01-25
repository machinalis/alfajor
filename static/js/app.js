$(document).ready(function(){
	//$("#app").slideToggle();
        if (toggle_cajas) {
          // if boxes presents for the session, then make it deletable
          $("#paneCartB a").unbind().click(function(){
	        tag=$(this).parent().parent().children(".inactivo:first");
		if(tag.is("li")){
			tag.before("<li></li>");
		}else{
			$(this).parent().parent().children("li:last").after("<li></li>");
		}
		$(this).parent().remove();

		organizar();

		return false;
          });
        }


	$("#selAlfajores").click(function(){
		$("#selBombones").removeClass("seleccionada");
		$(this).addClass("seleccionada");
		$("#t1").hide(); $("#t0").show();
		return false;
	});
	$("#selBombones").click(function(){
		$("#selAlfajores").removeClass("seleccionada");
		$(this).addClass("seleccionada");
		$("#t0").hide(); $("#t1").show();
		return false;
	});

	$("#paneA li a").click(function(){
		idR=$(this).attr("idR");
		$.ajax({
			url: "/alfajor/ajax/producto-por-id/",
			data: "idR="+idR,
			dataType: "json",
			cache: false,
		        success: function(res){
		          var variedad = res.variedad[0].toUpperCase() +
                            res.variedad.slice(1);
                          $("#paneB h1").html(variedad);
			  $("#paneB img").attr("src", res.imagen);
			  $("#paneB p").html(res.descripcion);
			  $("#precioItem strong").html(res.precio_por_unidad);
			  $("#idItemActivo").val(idR).attr("tipo", res.tipo);
			  $("#idItemActivo").val(idR).attr("precio", res.precio_por_unidad);
                          var last_choice = $("#paneA li a[idr='" +
                                          last_choice_id
                                          + "']");
                          var html = last_choice.children().first().html();
                          last_choice.empty();
                          last_choice.append(html);
                          var choice = $("#paneA li a[idr='" + idR + "']");
                          html =  choice.html();
                          choice.empty();
                          choice.append('<b>' + html + '</b>');
                          last_choice_id = idR;
                          itemParaAgregar = parseInt(res.pk);
			}
		});
		return false;
	});

	$("#selectCant").change(function(){
		agregarItems($(this).val());
		$(this)[0].selectedIndex = 0;
	});

	$("#accNuevaCaja").click(function(){
		idCaja=parseFloat($("#siguienteCaja").val());
		$("#siguienteCaja").val(idCaja+1);

		caja='<input type="hidden" name="cajas[]" class="cajas" caja="'+idCaja+'" tipo="" value="" activa="0">';
		ul='<ul id="detalleCaja_'+idCaja+'"><li></li><li></li><li></li><li></li><li></li><li></li><li></li><li></li><li></li><li></li><li></li><li></li><div class="clear"></div></ul>';
		a='<li><a href="#" caja="'+idCaja+'">Caja #'+idCaja+'</a></li>';

		$(".cajas:last").after(caja);
		$("#paneCartB ul:last").after(ul);
		$("#paneCartA ul li:last").after(a);

		$("#paneCartA ul li a").unbind().click(function(){
			activarCaja($(this).attr("caja"));
			return false;
		});

		activarCaja(idCaja);

		return false;
	});

	$("#accDuplicaCaja").click(function(){
		idCaja=parseFloat($("#siguienteCaja").val());
		$("#siguienteCaja").val(idCaja+1);

		idCajaActiva=cajaActiva();

		$('.cajas[caja="'+idCajaActiva+'"]').clone().attr("caja",idCaja).appendTo("form");
		$("#detalleCaja_"+idCajaActiva).clone().attr("id","detalleCaja_"+idCaja).appendTo("#paneCartB");
		$("#paneCartA ul li:last").after('<li><a href="#" caja="'+idCaja+'">Caja #'+idCaja+'</a></li>');

		$("#paneCartA ul li a").unbind().click(function(){
			activarCaja($(this).attr("caja"));
			return false;
		});

		activarCaja(idCaja);

		return false;
	});

	$("#accBorraCaja").click(function(){
		if($(".cajas").size()>1){
			if(confirm("Seguro que desea borrar la caja?")){
				idCajaActiva=cajaActiva();
				$('.cajas[caja="'+idCajaActiva+'"], #detalleCaja_'+idCajaActiva).remove();
				$('#paneCartA ul li a[caja="'+idCajaActiva+'"]').parent().remove();

				activarCaja($(".cajas:first").attr("caja"));
			}
		}else{
			alert("No es posible borrar esta caja, ya que al menos debe quedar una activa.");
		}
		return false;
	});

	$("#paneCartA a").click(function(){
		activarCaja($(this).attr("caja"));
		return false;
	});

	$("#siguiente").click(function(){
		if(todoOk()){
			$("form").submit();
		}else{
			alert("Las cajas deben contener 6 o 12 unidades. Por favor revise su pedido.");
		}
	});
});

function redondear(valor){
	var x = new Number(valor);
	return x.toFixed(2);
}

function cajaActiva(){
	$(".cajas").each(function(){
		if($(this).attr("activa")==1){
			res=$(this).attr("caja");
		}
	});
	return res;
}

function todoOk(){
	res=true;
	$(".cajas").each(function(){
		unidadesEnCaja=$(this).val().split(",");
		unidadesEnCaja=unidadesEnCaja.length-1;
		if(unidadesEnCaja>0 && unidadesEnCaja<6) res=false;
		if(unidadesEnCaja>6 && unidadesEnCaja<12) res=false;
	});
	return res;
}

function activarCaja(idCaja){
	$(".cajas").attr("activa","0");
	$("#paneCartB ul").hide();
	$('.cajas[caja="'+idCaja+'"]').attr("activa","1");
	$("#detalleCaja_"+idCaja).show();

	$("#paneCartA ul li a").removeClass('selected');
	$('#paneCartA ul li a[caja="'+idCaja+'"]').addClass('selected');

	organizar();
}

function agregarItems(cant){
	cant=parseFloat(cant);
	itemId=itemParaAgregar;
	itemNombre=$("#paneB h1").text();
	itemTipo=$("#idItemActivo").attr("tipo");
	itemPrecio=$("#idItemActivo").attr("precio");

	cajaActivaCab=$('.cajas[caja="'+cajaActiva()+'"]');
	cajaActivaDet=$("#detalleCaja_"+cajaActiva());

	unidadesEnCaja=cajaActivaCab.val().split(",");
	unidadesEnCaja=unidadesEnCaja.length-1;

	if(unidadesEnCaja==0) cajaActivaCab.attr("tipo",itemTipo);

	agregar=cant;
	if(unidadesEnCaja<12){
		if((unidadesEnCaja+cant)>12) agregar=(12-unidadesEnCaja);
	}else{
		alert("Esta caja ya esta completa.");
		agregar=0;
	}

	if(agregar>0){
		if(itemTipo==cajaActivaCab.attr("tipo")){
			for(i=0;i<agregar;i++){
				cajaActivaDet.children(":empty:first").
                                  addClass("idR"+itemId).attr("itemId",itemId).
                                    attr("itemPrecio",itemPrecio).
                                      html('<a href="#">x</a><p>'+itemNombre+'</p>');
			}
			organizar();
		}else{
			alert("Las cajas deben contener productos del mismo tipo.");
		}
	}
}

function organizar(){
	$("#paneCartB a").unbind().click(function(){
	        tag=$(this).parent().parent().children(".inactivo:first");

		if(tag.is("li")){
			tag.before("<li></li>");
		}else{
			$(this).parent().parent().children("li:last").after("<li></li>");
		}
		$(this).parent().remove();

		organizar();

		return false;
	});

	total=0;
	$(".cajas").each(function(){
		contenidoCaja=""; i=0;
		$("#detalleCaja_"+$(this).attr("caja")+" li[itemPrecio]").each(function(){
			itemPrecio=parseFloat($(this).attr("itemPrecio"));
			total=total+itemPrecio;
			contenidoCaja=contenidoCaja+$(this).attr("itemId")+",";
			i++;
		});
		$(this).val(contenidoCaja);

		if(i>=0 && i<6){
			$("#detalleCaja_"+$(this).attr("caja")+" li:gt(5)").addClass("inactivo");
		}else if(i>5){
			$("#detalleCaja_"+$(this).attr("caja")+" li").removeClass("inactivo");
		}
	});

	$("#panePrice strong").text(redondear(total));
}
