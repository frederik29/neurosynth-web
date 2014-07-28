# Place all the behaviors and hooks related to the matching controller here.
# All this logic will automatically be available in application.js.
# You can use CoffeeScript in this file: http://jashkenas.github.com/coffee-script/
$(document).ready ->
  # $('#decode_form').submit( (e) ->
  #   window.location.replace('/decode/' + $('#neurovault_id').val())
  #   e.preventDefault()
  # )

  if $('#page-decode-show').length

    loadImages()

    tbl = $('#decoding_results_table').DataTable()
    tbl.ajax.url('/decode/' + image_id + '/data').load()

    last_row_selected = null
    $('#decoding_results_table').on('click', 'button', (e) =>
      row = $(e.target).closest('tr')
      $(last_row_selected).children('td').removeClass('highlight-table-row')
      $(row).children('td').addClass('highlight-table-row')
      last_row_selected = row
      feature = $('td:eq(1)', row).text()
      imgs = load_reverse_inference_image(feature)
      viewer.loadImages(imgs)
      $(viewer).off('imagesLoaded')
      $(viewer).on('imagesLoaded', (e) ->
        viewer.deleteLayer(1)  if viewer.layerList.layers.length == 4
      )
      # Load scatterplot
      $('#scatterplot').html('<img src="/decode/' + image_id + '/scatter/' + feature + '.png" width="500px">')
    )

    $(viewer).on("afterLocationChange", (evt, data) ->
      if scatter?
        xv = viewer.getValue(1, data.ijk, space='image')
        yv = viewer.getValue(0, data.ijk, space='image')
        scatter.select(xv, yv)
      )

  else if $('#page-decode-index').length

    $('#neurovault-button').click( ->
      window.location.href = 'http://neurovault.org/images/add_for_neurosynth'
      )

  # $('#decode-tab-menu a:first').tab('show')

  # $(viewer).on('imagesLoaded', () -> scatter()) if scatterplot
