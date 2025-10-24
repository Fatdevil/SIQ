using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.UI;

namespace SIQ.ARHUD
{
    public sealed class ScoreHud : MonoBehaviour
    {
        [SerializeField]
        private HitDetector hitDetector = default!;

        [SerializeField]
        private Text? scoreText;

        [SerializeField]
        private Text? comboText;

        [SerializeField]
        private Image? lockIcon;

        [SerializeField]
        private UnityEvent<float>? onScoreChanged;

        private readonly Queue<float> _recentScores = new();
        private float _totalScore;

        private void Awake()
        {
            if (hitDetector != null)
            {
                hitDetector.Hit += OnTargetHit;
            }
        }

        private void OnDestroy()
        {
            if (hitDetector != null)
            {
                hitDetector.Hit -= OnTargetHit;
            }
        }

        public void SetLockState(bool isLocked)
        {
            if (lockIcon != null)
            {
                lockIcon.enabled = isLocked;
            }
        }

        private void OnTargetHit(HitTelemetry telemetry)
        {
            _totalScore += telemetry.Score;
            _recentScores.Enqueue(telemetry.Score);

            while (_recentScores.Count > 5)
            {
                _recentScores.Dequeue();
            }

            if (scoreText != null)
            {
                scoreText.text = _totalScore.ToString("0");
            }

            if (comboText != null)
            {
                comboText.text = $"x{_recentScores.Count}";
            }

            onScoreChanged?.Invoke(_totalScore);
        }
    }
}
