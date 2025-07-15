DONE:
Delete "DefectBacklog" file

Sugar = 0 in output file for 6/24 going forward.  Correct from 6/21 - 6/23. (came back with 7/1 data?)
  7/12: Because value is "Sugar" instead of "Total Sugar"; no "Sugar" alone in file.  Changed YAML from 6/21 to 6/24, no impact.
        Need to learn why "Sugar" lines are eliminated from the result.  I thought it was because it was not present in the first file (6-21)
  7/15: FIX - Updated nutrition.py by adding "Sugar" to list of nutrients.  Any nutrient not listed here will not be in file.

TO DO:
Combine "Total Sugar" and "Sugar" into a single value.
