"use client";

import { Spinner } from "@fluentui/react-components";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { PipelineBuilder } from "@/components/pipeline/PipelineBuilder";

function BuilderRoute() {
  const { pipelineId } = useParams<{ pipelineId: string }>();
  const tab = useSearchParams().get("tab") ?? "canvas";
  return <PipelineBuilder pipelineId={pipelineId} tab={tab} />;
}

export default function PipelineBuilderPage() {
  return (
    <Suspense fallback={<Spinner label="Loading builder…" />}>
      <BuilderRoute />
    </Suspense>
  );
}
