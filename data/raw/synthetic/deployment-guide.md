---
document_id: ENG-001
title: Production Deployment Guide
department: engineering
document_type: runbook
version: "1.0"
status: active
effective_date: "2026-10-01"
source_type: synthetic
language: en
---

# Production Deployment Guide

## Before deployment

Every production deployment requires approval from the release owner.
The engineer must confirm that automated tests have passed and that
a rollback package is available.

## Deployment verification

After deployment, monitor the service for 15 minutes.
Check the error rate, request latency, and health endpoint.

## Rollback conditions

Rollback is required if the error rate exceeds 5% for five consecutive
minutes or if the health endpoint fails three consecutive checks.

The on-call engineer performs the rollback and informs the release owner.

## After rollback

Create an incident report within 24 hours.
Include the deployment version, observed symptoms, rollback time,
and verification results.