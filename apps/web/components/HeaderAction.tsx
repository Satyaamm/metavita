"use client";

import { Button } from "@fluentui/react-components";
import { AddRegular } from "@fluentui/react-icons";
import Link from "next/link";

/** A primary header CTA that routes to a create flow. */
export function HeaderAction({ href, label }: { href: string; label: string }) {
  return (
    <Link href={href}>
      <Button appearance="primary" icon={<AddRegular />}>
        {label}
      </Button>
    </Link>
  );
}
