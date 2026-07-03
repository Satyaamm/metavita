// The deep glyph components (`…/components/Color|Mono`) ship without their own
// .d.ts; declare them as React components taking a `size` prop.
declare module "@lobehub/icons/es/*" {
  import type { ComponentType } from "react";
  const Icon: ComponentType<{ size?: number; className?: string }>;
  export default Icon;
}
