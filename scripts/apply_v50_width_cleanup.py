# Width cleanup intentionally performs no geometry rewrite.
#
# The previous pass rebuilt the proven box-clamp mechanism inboard and caused
# multiple mechanical regressions (weakened base regions, altered clamp thrust
# geometry, extra service holes and reoriented threaded hardware). Width is now
# handled only after the restored mechanism has passed its functional gates.
print('Width cleanup: geometry rewrite disabled; preserve proven clamp mechanics')
