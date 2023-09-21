from pyodide.ffi import create_proxy, to_js
from js import THREE
from js import Object
from js import performance
import js
import asyncio
import yaml
import numpy as np

rM0 = 4.60  # Initial radius of Mercury orbit, in units of R0
vM0 = 5.10e-1  # Initial orbital speed of Mercury, in units of R0/T0
c_a = 9.90e-1  # Base acceleration of Mercury, in units of R0**3/T0**2
rS = 2.95e-7  # Schwarzschild radius of Sun,in units of R0
rL2 = 8.19e-7  # Specific angular momentum, in units of R0**2

dt = 2. * vM0 / c_a / 20  # Time step
alpha = 1.e6  # Strength of 1/r**3 term
beta = 0.0  # Strength of 1/r**4 term

scale = 0.25  # multiply all lengths by this to fit the viewport (TODO)


def build_renderer() -> THREE.WebGLRenderer:
    renderer = THREE.WebGLRenderer.new({"antialias": True})
    renderer.setSize(800, 800)
    renderer.shadowMap.enabled = False
    # renderer.setSize(js.window.innerWidth, js.window.innerHeight)
    return renderer


def init_canvas(renderer):
    canvas, = js.document.getElementsByName("render-box")
    canvas.replaceChildren(renderer.domElement)


def build_camera(scene: THREE.Scene) -> THREE.PerspectiveCamera:
    # camera = THREE.PerspectiveCamera.new(35, js.window.innerWidth / js.window.innerHeight, 1, 500)
    camera = THREE.OrthographicCamera.new(-2, 2, -2, 2, 1, 1000)
    camera.aspect = js.window.innerWidth / js.window.innerHeight
    camera.updateProjectionMatrix()
    camera.position.set(0, 0, 3)
    camera.lookAt(scene.position)
    return camera


def build_scene() -> THREE.Scene:
    scene = THREE.Scene.new()
    scene.background = THREE.Color.new("#000000")
    return scene


def build_sun(*, radius: float = 0.1, width_segments: int = 32, height_segments: int = 16) -> THREE.Mesh:
    params = {"color": "#aa9900"}
    params = Object.fromEntries(to_js(params))
    material = THREE.MeshMatcapMaterial.new(params)
    geometry = THREE.SphereGeometry.new(radius, width_segments, height_segments)
    sphere = THREE.Mesh.new(geometry, material)
    sphere.position.set(0, 0, 0)
    return sphere


def build_planet(*, position, radius: float = 0.05, width_segments: int = 32, height_segments: int = 16) -> THREE.Mesh:
    params = {"color": "#993333"}
    params = Object.fromEntries(to_js(params))
    material = THREE.MeshStandardMaterial.new(params)
    geometry = THREE.SphereGeometry.new(radius, width_segments, height_segments)
    sphere = THREE.Mesh.new(geometry, material)
    sphere.position.set(*position)
    return sphere


def make_lights():
    ambient_light = THREE.AmbientLight.new(0xFFFFFF, 1)

    camera_light = THREE.RectAreaLight.new(0xffffff, 10, 10, 10)
    camera_light.position.set(0, 0, 3)
    camera_light.lookAt(0, 0, 0)

    sun_light = THREE.PointLight.new(0xaa9900, 4)
    sun_light.position.set(0, 0, 0)

    return ambient_light, camera_light, sun_light


def evolve_mercury(vec_rM_old, vec_vM_old, alpha, beta):
    r_old_mag = np.linalg.norm(vec_rM_old)
    v_old_mag = np.linalg.norm(vec_vM_old)

    # Compute the factor coming from General Relativity
    fact = 1 + alpha * rS / v_old_mag + beta * rL2 / r_old_mag ** 2
    # Compute the absolute value of the acceleration
    aMS = c_a * fact / r_old_mag ** 2
    # Multiply by the direction to get the acceleration vector
    vec_aMS = - aMS * (vec_rM_old / r_old_mag)
    # Update velocity vector
    vec_vM_new = vec_vM_old + vec_aMS * dt
    # Update position vector
    vec_rM_new = vec_rM_old + vec_vM_new * dt
    return vec_rM_new, vec_vM_new


async def main():
    renderer = build_renderer()
    init_canvas(renderer)
    scene = build_scene()
    camera = build_camera(scene)

    for light in make_lights():
        scene.add(light)

    p = np.array([0, rM0, 0])
    v = np.array([vM0, 0, 0])

    sun = build_sun()
    mercury = build_planet(position=(p[0] * scale, p[1] * scale, p[2] * scale))
    scene.add(sun)
    scene.add(mercury)

    MAX_POINTS = 5000
    positions = js.Float32Array.new(MAX_POINTS * 3)
    line_geom = THREE.BufferGeometry.new()
    line_geom.setAttribute('position', THREE.BufferAttribute.new(positions, 3))
    draw_count = 0
    line_geom.setDrawRange(0, draw_count * 3)

    line_material = THREE.LineBasicMaterial.new({"color": 0xff00ff})
    line = THREE.Line.new(line_geom, line_material)
    scene.add(line)

    while True:
        p, v = evolve_mercury(p, v, alpha, beta)
        mercury.position.set(*(p * scale))

        if draw_count < MAX_POINTS:
            positions[draw_count * 3 + 0] = p[0] * scale
            positions[draw_count * 3 + 1] = p[1] * scale
            positions[draw_count * 3 + 2] = p[2] * scale - 2  # move behind planet
            draw_count += 1
            line.geometry.setDrawRange(0, draw_count)
            line.geometry.attributes.position.needsUpdate = True

        renderer.render(scene, camera)
        await asyncio.sleep(0.01)


main()
