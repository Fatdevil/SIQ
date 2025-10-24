using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.UI;
using UnityEngine.XR.ARFoundation;

[assembly: InternalsVisibleTo("Assembly-CSharp-Editor")]

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
        private Bounds _targetLocalBounds = new(Vector3.zero, Vector3.zero);
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

            _targetLocalBounds = ResolveLocalBounds(_spawnedTarget.transform);

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

            var localBounds = _targetLocalBounds.size == Vector3.zero
                ? ResolveLocalBounds(transform)
                : _targetLocalBounds;

            var projected = WorldRectToScreenPolygon(transform, localBounds, camera);
            polygon.AddRange(projected);

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

        private static Bounds ResolveLocalBounds(Transform target)
        {
            var meshFilter = target.GetComponent<MeshFilter>();
            if (meshFilter != null && meshFilter.sharedMesh != null)
            {
                return meshFilter.sharedMesh.bounds;
            }

            var renderer = target.GetComponent<Renderer>() ?? target.GetComponentInChildren<Renderer>();
            if (renderer == null)
            {
                return new Bounds(Vector3.zero, Vector3.one);
            }

            return ApproximateLocalBoundsFromRenderer(target, renderer);
        }

        private static Bounds ApproximateLocalBoundsFromRenderer(Transform target, Renderer renderer)
        {
            var worldBounds = renderer != null ? renderer.bounds : new Bounds(target.position, Vector3.one);
            var right = target.right.normalized;
            var up = target.up.normalized;

            var corners = new Vector3[]
            {
                worldBounds.center + new Vector3(+worldBounds.extents.x, +worldBounds.extents.y, +worldBounds.extents.z),
                worldBounds.center + new Vector3(+worldBounds.extents.x, +worldBounds.extents.y, -worldBounds.extents.z),
                worldBounds.center + new Vector3(+worldBounds.extents.x, -worldBounds.extents.y, +worldBounds.extents.z),
                worldBounds.center + new Vector3(+worldBounds.extents.x, -worldBounds.extents.y, -worldBounds.extents.z),
                worldBounds.center + new Vector3(-worldBounds.extents.x, +worldBounds.extents.y, +worldBounds.extents.z),
                worldBounds.center + new Vector3(-worldBounds.extents.x, +worldBounds.extents.y, -worldBounds.extents.z),
                worldBounds.center + new Vector3(-worldBounds.extents.x, -worldBounds.extents.y, +worldBounds.extents.z),
                worldBounds.center + new Vector3(-worldBounds.extents.x, -worldBounds.extents.y, -worldBounds.extents.z),
            };

            float minR = float.PositiveInfinity;
            float maxR = float.NegativeInfinity;
            float minU = float.PositiveInfinity;
            float maxU = float.NegativeInfinity;

            foreach (var corner in corners)
            {
                var toCorner = corner - target.position;
                var projectedRight = Vector3.Dot(toCorner, right);
                var projectedUp = Vector3.Dot(toCorner, up);
                minR = Mathf.Min(minR, projectedRight);
                maxR = Mathf.Max(maxR, projectedRight);
                minU = Mathf.Min(minU, projectedUp);
                maxU = Mathf.Max(maxU, projectedUp);
            }

            var safeScaleX = Mathf.Max(1e-6f, target.lossyScale.x);
            var safeScaleY = Mathf.Max(1e-6f, target.lossyScale.y);

            var sizeX = Mathf.Max(0.001f, (maxR - minR) / safeScaleX);
            var sizeY = Mathf.Max(0.001f, (maxU - minU) / safeScaleY);

            return new Bounds(Vector3.zero, new Vector3(sizeX, sizeY, 0.001f));
        }

        /// <summary>
        /// Computes the four local-space corners of the target quad using per-axis extents. Avoids diagonal-based scaling
        /// because Renderer.bounds.size.magnitude overestimates the footprint and causes hit leakage.
        /// </summary>
        /// <param name="target">Target transform providing lossy scale.</param>
        /// <param name="localMeshBounds">Mesh bounds in local space.</param>
        internal static Vector3[] BuildLocalRectCorners(Transform target, Bounds localMeshBounds)
        {
            var halfWidth = localMeshBounds.extents.x * target.lossyScale.x;
            var halfHeight = localMeshBounds.extents.y * target.lossyScale.y;

            return new[]
            {
                new Vector3(-halfWidth, -halfHeight, 0f),
                new Vector3(-halfWidth,  halfHeight, 0f),
                new Vector3( halfWidth,  halfHeight, 0f),
                new Vector3( halfWidth, -halfHeight, 0f),
            };
        }

        /// <summary>
        /// Projects the target quad to screen space using per-axis extents derived from the mesh bounds to preserve
        /// the true rectangle footprint under arbitrary scale/rotation.
        /// </summary>
        /// <param name="target">Transform anchoring the target.</param>
        /// <param name="localMeshBounds">Mesh bounds in local coordinates.</param>
        /// <param name="camera">Camera used for projection.</param>
        internal static List<Vector2> WorldRectToScreenPolygon(Transform target, Bounds localMeshBounds, Camera camera)
        {
            var localCorners = BuildLocalRectCorners(target, localMeshBounds);
            var polygon = new List<Vector2>(localCorners.Length);
            for (int i = 0; i < localCorners.Length; i++)
            {
                var worldCorner = target.TransformPoint(localCorners[i]);
                polygon.Add((Vector2)camera.WorldToScreenPoint(worldCorner));
            }

            return polygon;
        }
    }
}
