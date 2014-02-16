class Dashing.ProgressBars extends Dashing.Widget
 
  @accessor 'title'
 
  ready: ->
    @drawWidget( @get('progress_items') )
 
  onData: (eventData) ->
    @drawWidget(eventData.progress_items)
 
  drawWidget: (progress_items) ->
    container = $(@node)
    rowsContainer = container.find('.rows-container')
 
    if progress_items.length == 0
      rowsContainer.empty()
    else
      # Float value used to scale the rows to use the entire space of the widget
      rowHeight = 100 / progress_items.length
      counter = 0
      @clearIntervals()
 
      # Add or move rows for each project. Checks first if the row already exists.
      progress_items.forEach (item) =>
        normalizedItemName = item.name.replace(/\W+/g, "_")
        referenceRow = rowsContainer.children().eq(counter)
        existingRow = rowsContainer.find("."+normalizedItemName)
 
        if existingRow.length
          if referenceRow.attr("class").indexOf(normalizedItemName) == -1
            existingRow.detach().insertBefore(referenceRow)
            existingRow.hide().fadeIn(1200)
        else
          row = createRow(item)
          if referenceRow.length
            row.insertBefore(referenceRow)
          else
            rowsContainer.append(row)
          row.hide().fadeIn(1200)
 
        elem = rowsContainer.find("."+normalizedItemName+" .inner-progress-bar")
        if elem.length
          @animateProgressBarContent(elem[0], parseFloat(elem[0].style.width),
                                    parseFloat(item.progress), 1000)
        ++counter
 
      # Remove any nodes that were not in the new data, these will be the rows
      # at the end of the widget.
      currentNode = rowsContainer.children().eq(counter-1)
      while currentNode.next().length
        currentNode = currentNode.next()
        currentNode.fadeOut(100, -> $(this).remove() )
 
      # Set the height after rows were added/removed.
      rows = rowsContainer.children()
      percentageOfTotalHeight = 100 / progress_items.length
      applyCorrectedRowHeight(rows, percentageOfTotalHeight)
 
      applyZebraStriping(rows)
 
 
  #***/
  # Create a JQuery row object with the proper structure and base
  # settings for the item passed in.
  #
  # The Row DOM Hierarchy:
  # Row
  #   Row Content (here so we can use vertical alignment)
  #     Project Name
  #     Outer Bar Container (The border and background)
  #       Inner Bar Container (The progress and text)
  #
  # @item - object representing an item and it's progress
  # /
  createRow = (item) ->
 
    row = ( $("<div/>")
      .attr("class", "row " + item.name.replace(/\W+/g, "_") ) )
 
    rowContent = ( $("<div/>")
      .attr("class", "row-content") ) 
 
    projectName = ( $("<div/>")
      .attr("class", "project-name")
      .text(item.name)
      .attr("title", item.name) )
 
    outerProgressBar = ( $("<div/>")
      .attr("class", "outer-progress-bar") )
 
    innerProgressBar = $("<div/>")
      .attr("class", "inner-progress-bar")
      .text("0%")
    innerProgressBar.css("width", "0%")
 
    # Put it all together.
    outerProgressBar.append(innerProgressBar)
    rowContent.append(projectName)
    rowContent.append(outerProgressBar)
    row.append(rowContent)
 
    return row
 
 
  #***/
  # Does calculations for the animation and sets up the javascript
  # interval to perform the animation.
  #
  # @element - element that is going to be animated.
  # @from - the value that the element starts at.
  # @to - the value that the element is going to.
  # @baseDuration - the minimum time the animation will perform.
  # /
  animateProgressBarContent: (element, from, to, baseDuration) ->
    endpointDifference = (to-from)
 
    if endpointDifference != 0
      currentValue = from
 
      # Every x milliseconds, the function should run.
      stepInterval = 16.667
 
      # Change the duration based on the distance between points.
      duration = baseDuration + Math.abs(endpointDifference) * 25
 
      numberOfSteps = duration / stepInterval
      valueIncrement = endpointDifference / numberOfSteps
      
      interval = setInterval(
        ->
          currentValue += valueIncrement
          if Math.abs(currentValue - from) >= Math.abs(endpointDifference)
            setProgressBarValue(element, to)
            clearInterval(interval)
          else
            setProgressBarValue(element, currentValue)
        stepInterval)
 
      @addInterval(interval)
 
  #***/
  # Sets the text and width of the element in question to the specified value
  # after making sure it is bounded between [0-100]
  #
  # @element - element to be set
  # @value - the numeric value to set the element to. This can be a float.
  # /
  setProgressBarValue = (element, value) ->
    if (value > 100) 
      value = 100
    else if (value < 0) 
      value = 0
    element.textContent = Math.floor(value) + "%"
    element.style.width = value + "%"
 
  #***/
  # Applies a percentage-based row height to the list of rows passed in.
  #
  # @rows - the elements to apply this height value to
  # @percentageOfTotalHeight - The height to be applied to each row.
  # /
  applyCorrectedRowHeight = (rows, percentageOfTotalHeight) ->
    height = percentageOfTotalHeight + "%"
    for row in rows
      row.style.height = height
 
  #***/
  # Adds a class to every other row to change the background color. This
  # was done mainly for readability.
  #
  # @rows - list of elements to run zebra-striping on
  # /
  applyZebraStriping = (rows) ->
    isZebraStripe = false
    for row in rows
      # In case elements are moved around, we don't want them to retain this.
      row.classList.remove("zebra-stripe")
      if isZebraStripe
        row.classList.add("zebra-stripe")
      isZebraStripe = !isZebraStripe
 
  #***/
  # Stops all javascript intervals from running and clears the list.
  #/
  clearIntervals: ->
    if @intervalList
      for interval in @intervalList
        clearInterval(interval)
      @intervalList = []
 
  #***/
  # Adds a javascript interval to a list so that it can be tracked and cleared
  # ahead of time if the need arises.
  #
  # @interval - the javascript interval to add
  #/
  addInterval: (interval) ->
    if !@intervalList
      @intervalList = []
    @intervalList.push(interval)