using System;
using System.Collections.Generic;
using UnityEngine;

namespace SIQ.ARHUD
{
    [Serializable]
    public struct HitTelemetry
    {
        public string TargetId;
        public Vector2 HitPoint2D;
        public Vector3 HitPoint3D;
        public float Score;
    }

    public sealed class HitDetector : MonoBehaviour
    {
        [SerializeField]
        private TargetAnchor targetAnchor = default!;

        [SerializeField]
        private Camera arCamera = default!;

        [SerializeField]
        private ParticleSystem? hitParticles;

        [SerializeField]
        private AudioSource? hitAudio;

        [SerializeField]
        private string targetId = "range-target";

        [SerializeField]
        private float hitCooldownSeconds = 0.35f;

        [SerializeField]
        private float maxScoreRadius = 0.65f;

        private readonly List<Vector2> _projectedPolygon = new();
        private float _lastHitTime = -10f;

        public event Action<HitTelemetry>? Hit;

        private void OnEnable()
        {
            _lastHitTime = -hitCooldownSeconds;
        }

        public void ProcessBallSample(Vector3 worldSample)
        {
            if (targetAnchor == null || arCamera == null)
            {
                return;
            }

            if (!targetAnchor.TryGetTargetPolygon(arCamera, _projectedPolygon))
            {
                return;
            }

            var screenPoint = (Vector2)arCamera.WorldToScreenPoint(worldSample);
            if (!PointInPolygon(screenPoint, _projectedPolygon))
            {
                return;
            }

            if (!targetAnchor.TryGetAnchorPlane(out var plane))
            {
                return;
            }

            var ray = arCamera.ScreenPointToRay(screenPoint);
            if (!plane.Raycast(ray, out var enter))
            {
                return;
            }

            var worldHit = ray.GetPoint(enter);
            var time = Time.unscaledTime;
            if (time - _lastHitTime < hitCooldownSeconds)
            {
                return;
            }

            _lastHitTime = time;
            var score = ComputeScore(worldHit);
            PlayEffects(worldHit);

            var telemetry = new HitTelemetry
            {
                TargetId = targetId,
                HitPoint2D = screenPoint,
                HitPoint3D = worldHit,
                Score = score,
            };

            Hit?.Invoke(telemetry);
        }

        private float ComputeScore(Vector3 worldHit)
        {
            if (targetAnchor.TargetTransform == null)
            {
                return 0f;
            }

            var center = targetAnchor.TargetTransform.position;
            var distance = Vector3.Distance(center, worldHit);
            var normalized = Mathf.Clamp01(1f - (distance / Mathf.Max(0.001f, maxScoreRadius)));
            return Mathf.Round(normalized * 100f);
        }

        private void PlayEffects(Vector3 worldPosition)
        {
            if (hitParticles != null)
            {
                hitParticles.transform.position = worldPosition;
                hitParticles.Play();
            }

            if (hitAudio != null)
            {
                hitAudio.transform.position = worldPosition;
                hitAudio.Play();
            }
        }

        private static bool PointInPolygon(Vector2 point, List<Vector2> polygon)
        {
            var windingNumber = 0;
            for (var i = 0; i < polygon.Count; i++)
            {
                var v1 = polygon[i];
                var v2 = polygon[(i + 1) % polygon.Count];

                if (v1.y <= point.y)
                {
                    if (v2.y > point.y && IsLeft(v1, v2, point) > 0)
                    {
                        windingNumber++;
                    }
                }
                else
                {
                    if (v2.y <= point.y && IsLeft(v1, v2, point) < 0)
                    {
                        windingNumber--;
                    }
                }
            }

            return windingNumber != 0;
        }

        private static float IsLeft(Vector2 a, Vector2 b, Vector2 c)
        {
            return ((b.x - a.x) * (c.y - a.y)) - ((c.x - a.x) * (b.y - a.y));
        }
    }
}
