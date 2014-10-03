# some ruby code

def _get_column_delimeter(delimeter, padding, padding_character)
  start, _, middle, last = _get_delimeter_info(delimeter, :column)

  space = (padding_character || ' ') * (padding || 0)

  start = start.empty?() ? start : start + space
  middle = middle.empty?() ? space : space + middle + space
  last = last.empty?() ? last : space + last

  # result will be extracted to variable
  return ColumnDelimeter.new(start, middle, last)
end

def _get_column_delimeter_length(options, columns = 1)
  delimeter = _get_column_delimeter(options[:delimeter], options[:padding],
    options[:padding_character])

  # variable will be detached
  length = delimeter.start.length + delimeter.middle.length *
    (columns - 1) + delimeter.last.length

  return length
end

def _get_maximal_column_width(options, columns_count, column_index)
  maximal = options[:maximal_column_width]
  maximal_alternative = _get_maximal_columns_width(options, columns_count,
    column_index)

  if maximal.nil?()
    maximal = maximal_alternative
  elsif !maximal_alternative.nil?() && maximal > maximal_alternative
    maximal = maximal_alternative
  end

  # variable will be renamed
  return maximal
end