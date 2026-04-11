# Axy Lusion Scheduled Refresh Handoff - 2026-04-11

## Outcome

- Axy Lusion now has real unattended refresh jobs.
- The site no longer depends on a person manually running the refresh path each day.
- Morning and evening runs are separated so news can refresh twice daily without needlessly re-syncing the A-List in the evening.

## What Was Added

- `scripts/run-scheduled-refresh.ps1`
  - morning mode runs the full refresh path
  - evening mode runs the lighter news-facing refresh path
- `scripts/refresh-site-data.ps1`
  - now supports `-SkipAList`
- `W:\Websites\schedules\jobs.psd1`
  - added `Websites-AxyLusion-Refresh-Morning`
  - added `Websites-AxyLusion-Refresh-Evening`
- Scheduler registration
  - tasks were registered via `W:\Websites\schedules\Register-ScheduledJobs.ps1`

## Schedule

- `Websites-AxyLusion-Refresh-Morning`
  - `07:20` daily
  - runs after upstream shared news and AI Resource Hub morning updates
- `Websites-AxyLusion-Refresh-Evening`
  - `19:20` daily
  - runs after the evening shared news cycle

## Evidence

- Manual wrapper verification:
  - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-scheduled-refresh.ps1 -Mode Morning`
  - `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/run-scheduled-refresh.ps1 -Mode Evening`
  - both succeeded
- Scheduler registration:
  - `W:\Websites\schedules\Show-ScheduledJobs.ps1`
  - both Axy jobs show as enabled and registered
- Scheduler execution proof:
  - `Start-ScheduledTask -TaskName 'Websites-AxyLusion-Refresh-Evening'`
  - `LastTaskResult = 0`
- Shared visibility:
  - runs land in `cron_job_history` with schedule names
    - `Websites-AxyLusion-Refresh-Morning`
    - `Websites-AxyLusion-Refresh-Evening`

## Risk

- The scheduled jobs will keep Axy fresh only as far as upstream sources are fresh.
- They deliberately do not duplicate:
  - `LLATOS Website News Cycle`
  - `AI Resource Hub - Daily Update`
- The remaining public launch blocker is still the external image-hosting cutover.

## Next Action

- None inside the Axy lane beyond the external items you already own:
  - Cloudflare R2 image cutover
  - custom domain connection
