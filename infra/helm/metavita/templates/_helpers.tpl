{{- define "metavita.labels" -}}
app.kubernetes.io/name: metavita
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{- define "metavita.env" -}}
- name: METAVITA_DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: {{ .Values.existingSecret }}
      key: databaseUrl
- name: METAVITA_REDIS_URL
  valueFrom:
    secretKeyRef:
      name: {{ .Values.existingSecret }}
      key: redisUrl
- name: METAVITA_S3_ENDPOINT_URL
  valueFrom:
    secretKeyRef:
      name: {{ .Values.existingSecret }}
      key: s3Endpoint
{{- end -}}
