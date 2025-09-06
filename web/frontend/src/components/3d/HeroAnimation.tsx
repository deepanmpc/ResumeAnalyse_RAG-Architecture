import { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Points, PointMaterial } from '@react-three/drei'
import * as THREE from 'three'

function Particles({ count = 5000 }) {
  const points = useRef<THREE.Points>(null!)

  const particles = useMemo(() => {
    const temp = []
    const t = 20000
    const a = 12
    const f = (t: number, a: number) => (t / a) * Math.PI * (3 - Math.sqrt(5))
    for (let i = 0; i < count; i++) {
      const t = Math.random() * 20000
      const r = Math.sqrt(t) / Math.sqrt(20000)
      const x = r * Math.cos(f(t, a))
      const y = r * Math.sin(f(t, a))
      const z = (Math.random() - 0.5) * 2
      temp.push(x, y, z)
    }
    return new Float32Array(temp)
  }, [count])

  useFrame((state) => {
    const time = state.clock.getElapsedTime()
    if (points.current) {
      points.current.rotation.z = time / 20
    }
  })

  return (
    <Points ref={points} positions={particles} stride={3} frustumCulled={false}>
      <PointMaterial
        transparent
        color="#4285f4"
        size={0.015}
        sizeAttenuation={true}
        depthWrite={false}
      />
    </Points>
  )
}

export function HeroAnimation() {
  return (
    <Canvas camera={{ position: [0, 0, 1.5] }}>
      <Particles />
    </Canvas>
  )
}
