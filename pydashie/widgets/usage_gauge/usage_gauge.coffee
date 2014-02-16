class Dashing.UsageGauge extends Dashing.Widget
	@accessor 'value', Dashing.AnimatedValue
 
	ready: ->
		$(@node).find(".value").before("<div class='gauge'></div>")
		$(@node).find(".gauge").append("<div class='gauge-meter'></div>")
		@meter = $(@node).find(".gauge-meter");
 
	onData: (data) ->
		@meter.animate({height: Batman.mixin Batman.Filters.percentage(data.value, @get("max")) + "%"})
 
	@accessor "total", ->
		@get("max")
 
	@accessor "suffix", ->
		" %"
 
Batman.mixin Batman.Filters,
	percentage: (n, total) ->
		Math.round(n * 100 / total)