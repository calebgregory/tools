;; extends

;; Python's highlights query captures a class name as @type both where the class
;; is DEFINED and everywhere it is referenced, which leaves no way to color the
;; definition differently from a use.  Re-capture the definition site as
;; @type.definition so minimal.lua can keep it yellow with the other "global
;; definitions" while every reference goes gray.
;;
;; Patterns from an after/ query run last, and the last capture on a range wins.
(class_definition name: (identifier) @type.definition)
