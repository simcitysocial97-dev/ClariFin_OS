"use client"

import * as React from "react"

function VisuallyHidden({
  className,
  ...props
}: React.ComponentProps<"span">) {
  return (
    <span
      className={className}
      style={{
        border: 0,
        clip: "rect(0 0 0 0)",
        clipPath: "inset(50%)",
        height: "1px",
        margin: "-1px",
        overflow: "hidden",
        padding: 0,
        position: "absolute",
        width: "1px",
        whiteSpace: "nowrap",
      }}
      {...props}
    />
  )
}

export { VisuallyHidden }