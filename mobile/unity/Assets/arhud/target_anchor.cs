using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.UI;
using UnityEngine.XR.ARFoundation;

namespace SIQ.ARHUD
{
    public enum TargetPlacementMode
    {
        AprilTag,
        Image,
        Plane,
    }

    public interface IAprilTagPoseSource
    {
        event Action<AprilTagPose> PoseUpdated;
        bool IsTracking { get; }
    }

    [Serializable]
    public struct AprilTagPose
    {
        public Pose Pose;
        public float Quality;
    }

    [RequireComponent(typeof(ARAnchorManager))]
    public sealed class TargetAnchor : MonoBehaviour
    {
        [Header("Placement")]
        [SerializeField]
        private TargetPlacementMode placementMode = TargetPlacementMode.AprilTag;

        [SerializeField]
        private GameObject targetPrefab = default!;

        [SerializeField]
        private MonoBehaviour? aprilTagSourceBehaviour;

        [SerializeField]
        private ARTrackedImageManager? trackedImageManager;

        [SerializeField]
        private ARRaycastManager? raycastManager;

        [SerializeField]
        private Camera? arCamera;

        [Header("UI")]
        [SerializeField]
        private Button? recenterButton;

        [SerializeField]
        private Image? trackingLockIcon;

        [SerializeField]
        private float trackingLockThreshold = 0.75f;

        [SerializeField]
        private UnityEvent onAnchorPlaced = new();

        private ARAnchorManager? _anchorManager;
        private ARAnchor? _currentAnchor;
        private GameObject? _spawnedTarget;
        private Renderer? _targetRenderer;
        private Bounds _targetBounds;
        private float _lastQuality;
        private Pose? _lastPose;
        private IAprilTagPoseSource? _aprilTagSource;

        private static readonly List<ARRaycastHit> s_RaycastHits = new();

        public Transform? TargetTransform => _spawnedTarget != null ? _spawnedTarget.transform : null;

        public float BoundingRadius => _targetBounds.extents.magnitude;

        public event Action<Pose>? AnchorRecentered;

        private void Awake()
        {
            _anchorManager = GetComponent<ARAnchorManager>();
            if (aprilTagSourceBehaviour != null)
            {
                _aprilTagSource = aprilTagSourceBehaviour as IAprilTagPoseSource;
                if (_aprilTagSource != null)
                {
                    _aprilTagSource.PoseUpdated += OnAprilTagPoseUpdated;
                }
            }

            if (trackedImageManager != null)
            {
                trackedImageManager.trackedImagesChanged += OnTrackedImagesChanged;
            }

            if (recenterButton != null)
            {
                recenterButton.onClick.AddListener(HandleRecenterRequested);
            }
        }

        private void OnDestroy()
        {
            if (_aprilTagSource != null)
            {
                _aprilTagSource.PoseUpdated -= OnAprilTagPoseUpdated;
            }

            if (trackedImageManager != null)
            {
                trackedImageManager.trackedImagesChanged -= OnTrackedImagesChanged;
            }

            if (recenterButton != null)
            {
                recenterButton.onClick.RemoveListener(HandleRecenterRequested);
            }
        }

        private void Update()
        {
            if (placementMode == TargetPlacementMode.Plane)
            {
                TryHandleTapPlacement();
            }

            UpdateLockIcon();
        }

        private void OnAprilTagPoseUpdated(AprilTagPose tagPose)
        {
            if (placementMode != TargetPlacementMode.AprilTag)
            {
                return;
            }

            _lastPose = tagPose.Pose;
            _lastQuality = tagPose.Quality;

            if (!_aprilTagSource!.IsTracking)
            {
                return;
            }

            PlaceAnchor(tagPose.Pose);
        }

        private void OnTrackedImagesChanged(ARTrackedImagesChangedEventArgs args)
        {
            if (placementMode != TargetPlacementMode.Image)
            {
                return;
            }

            foreach (var trackedImage in args.added)
            {
                PlaceAnchor(new Pose(trackedImage.transform.position, trackedImage.transform.rotation));
            }

            foreach (var trackedImage in args.updated)
            {
                if (trackedImage.trackingState == UnityEngine.XR.ARSubsystems.TrackingState.Tracking)
                {
                    PlaceAnchor(new Pose(trackedImage.transform.position, trackedImage.transform.rotation));
                }
            }
        }

        private void TryHandleTapPlacement()
        {
            if (raycastManager == null || arCamera == null)
            {
                return;
            }

            if (Input.touchCount == 0)
            {
                return;
            }

            var touch = Input.GetTouch(0);
            if (touch.phase != TouchPhase.Began)
            {
                return;
            }

            if (raycastManager.Raycast(touch.position, s_RaycastHits, UnityEngine.XR.ARSubsystems.TrackableType.Planes))
            {
                var hitPose = s_RaycastHits[0].pose;
                _lastPose = hitPose;
                _lastQuality = 1.0f;
                PlaceAnchor(hitPose);
            }
        }

        private void PlaceAnchor(Pose pose)
        {
            if (_anchorManager == null || targetPrefab == null)
            {
                return;
            }

            if (_currentAnchor != null)
            {
                Destroy(_currentAnchor.gameObject);
                _currentAnchor = null;
            }

            _currentAnchor = _anchorManager.AddAnchor(pose);
            if (_currentAnchor == null)
            {
                return;
            }

            if (_spawnedTarget != null)
            {
                Destroy(_spawnedTarget);
            }

            _spawnedTarget = Instantiate(targetPrefab, _currentAnchor.transform);
            _spawnedTarget.transform.localPosition = Vector3.zero;
            _spawnedTarget.transform.localRotation = Quaternion.identity;

            _targetRenderer = _spawnedTarget.GetComponentInChildren<Renderer>();
            if (_targetRenderer != null)
            {
                _targetBounds = _targetRenderer.bounds;
            }

            onAnchorPlaced.Invoke();
        }

        private void HandleRecenterRequested()
        {
            if (_lastPose.HasValue)
            {
                PlaceAnchor(_lastPose.Value);
                AnchorRecentered?.Invoke(_lastPose.Value);
            }
        }

        private void UpdateLockIcon()
        {
            if (trackingLockIcon == null)
            {
                return;
            }

            var quality = Mathf.Clamp01(_lastQuality);
            var isLocked = quality >= trackingLockThreshold;
            trackingLockIcon.enabled = isLocked;
        }

        public bool TryGetTargetPolygon(Camera camera, List<Vector2> polygon)
        {
            if (camera == null)
            {
                return false;
            }

            var transform = TargetTransform;
            if (transform == null)
            {
                return false;
            }

            polygon.Clear();

            var localCorners = new[]
            {
                new Vector3(-0.5f, -0.5f, 0f),
                new Vector3(-0.5f, 0.5f, 0f),
                new Vector3(0.5f, 0.5f, 0f),
                new Vector3(0.5f, -0.5f, 0f),
            };

            foreach (var corner in localCorners)
            {
                var worldCorner = transform.TransformPoint(corner * (_targetBounds.size.magnitude > 0 ? _targetBounds.size.magnitude : 1f));
                polygon.Add(camera.WorldToScreenPoint(worldCorner));
            }

            return polygon.Count == 4;
        }

        public bool TryGetAnchorPlane(out Plane plane)
        {
            plane = default;
            if (TargetTransform == null)
            {
                return false;
            }

            plane = new Plane(TargetTransform.up, TargetTransform.position);
            return true;
        }
    }
}
