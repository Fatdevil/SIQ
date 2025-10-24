using NUnit.Framework;
using UnityEngine;

namespace SIQ.ARHUD.Tests
{
    public class TargetAnchorPolygonTests
    {
        [Test]
        public void BuildLocalRectCorners_UsesWidthHeight_NotDiagonal()
        {
            var go = new GameObject("target");
            try
            {
                var t = go.transform;
                t.position = Vector3.zero;
                t.localScale = Vector3.one;

                var bounds = new Bounds(Vector3.zero, new Vector3(2f, 1f, 0f));
                var corners = TargetAnchor.BuildLocalRectCorners(t, bounds);

                Assert.That(corners, Has.Length.EqualTo(4));
                Assert.That(corners[0].x, Is.EqualTo(-1f).Within(1e-4f));
                Assert.That(corners[0].y, Is.EqualTo(-0.5f).Within(1e-4f));
                Assert.That(corners[1].x, Is.EqualTo(-1f).Within(1e-4f));
                Assert.That(corners[1].y, Is.EqualTo(0.5f).Within(1e-4f));
                Assert.That(corners[2].x, Is.EqualTo(1f).Within(1e-4f));
                Assert.That(corners[2].y, Is.EqualTo(0.5f).Within(1e-4f));
                Assert.That(corners[3].x, Is.EqualTo(1f).Within(1e-4f));
                Assert.That(corners[3].y, Is.EqualTo(-0.5f).Within(1e-4f));
            }
            finally
            {
                Object.DestroyImmediate(go);
            }
        }

        [Test]
        public void WorldRectToScreenPolygon_RotationKeepsFootprint()
        {
            var targetGo = new GameObject("target");
            var cameraGo = new GameObject("camera");
            try
            {
                var t = targetGo.transform;
                t.position = Vector3.zero;
                t.rotation = Quaternion.Euler(0f, 0f, 45f);
                t.localScale = new Vector3(2f, 1f, 1f);

                var camera = cameraGo.AddComponent<Camera>();
                camera.orthographic = true;
                camera.orthographicSize = 5f;
                camera.nearClipPlane = 0.01f;
                camera.farClipPlane = 100f;
                camera.pixelRect = new Rect(0f, 0f, 1000f, 1000f);
                camera.transform.position = new Vector3(0f, 0f, -10f);
                camera.transform.rotation = Quaternion.identity;

                var bounds = new Bounds(Vector3.zero, new Vector3(2f, 1f, 0f));
                var polygon = TargetAnchor.WorldRectToScreenPolygon(t, bounds, camera);

                Assert.That(polygon, Has.Count.EqualTo(4));

                var edgeHeight = (polygon[1] - polygon[0]).magnitude;
                var edgeWidth = (polygon[2] - polygon[1]).magnitude;

                var pixelsPerUnit = camera.pixelHeight / (camera.orthographicSize * 2f);
                var expectedHeight = bounds.size.y * t.lossyScale.y * pixelsPerUnit;
                var expectedWidth = bounds.size.x * t.lossyScale.x * pixelsPerUnit;

                Assert.That(edgeHeight, Is.EqualTo(expectedHeight).Within(1e-3f));
                Assert.That(edgeWidth, Is.EqualTo(expectedWidth).Within(1e-3f));
            }
            finally
            {
                Object.DestroyImmediate(targetGo);
                Object.DestroyImmediate(cameraGo);
            }
        }
    }
}
