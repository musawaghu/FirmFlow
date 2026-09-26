"use client"

import { Canvas } from "@react-three/fiber"
import { OrbitControls, Environment, ContactShadows } from "@react-three/drei"
import { Suspense } from "react"

function Warehouse() {
  // steel frame color, wall color, roof color
  const steel = "#8a9299"
  const wall = "#d9dee2"
  const roof = "#5a6169"
  const accent = "#e8863b"

  const bays = [-6, -2, 2, 6]

  return (
    <group position={[0, 0, 0]}>
      {/* Concrete slab / ground */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} receiveShadow>
        <planeGeometry args={[26, 18]} />
        <meshStandardMaterial color="#c3cbd1" />
      </mesh>

      {/* Painted floor lanes */}
      {[-3, 3].map((z) => (
        <mesh key={z} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.01, z]}>
          <planeGeometry args={[16, 0.25]} />
          <meshStandardMaterial color={accent} />
        </mesh>
      ))}

      {/* Main building group */}
      <group position={[0, 0, 0]}>
        {/* Side walls */}
        <mesh position={[0, 3, -4]} castShadow receiveShadow>
          <boxGeometry args={[16, 6, 0.3]} />
          <meshStandardMaterial color={wall} />
        </mesh>
        <mesh position={[0, 3, 4]} castShadow receiveShadow>
          <boxGeometry args={[16, 6, 0.3]} />
          <meshStandardMaterial color={wall} />
        </mesh>
        {/* Back wall */}
        <mesh position={[-8, 3, 0]} castShadow receiveShadow>
          <boxGeometry args={[0.3, 6, 8]} />
          <meshStandardMaterial color={wall} />
        </mesh>

        {/* Corrugated wall ribs (front-facing side wall) */}
        {Array.from({ length: 15 }).map((_, i) => (
          <mesh key={`rib-${i}`} position={[-7.5 + i, 3, 4.18]}>
            <boxGeometry args={[0.08, 5.6, 0.08]} />
            <meshStandardMaterial color={steel} />
          </mesh>
        ))}

        {/* Roof (gently pitched) */}
        <mesh position={[0, 6.4, 0]} castShadow>
          <boxGeometry args={[16.6, 0.3, 8.6]} />
          <meshStandardMaterial color={roof} metalness={0.3} roughness={0.6} />
        </mesh>
        {/* Roof accent stripe */}
        <mesh position={[0, 6.57, 0]}>
          <boxGeometry args={[16.6, 0.06, 1.2]} />
          <meshStandardMaterial color={accent} />
        </mesh>

        {/* Roof support columns */}
        {[-7.5, -3.75, 0, 3.75, 7.5].map((x) => (
          <mesh key={`col-${x}`} position={[x, 3, 0]} castShadow>
            <boxGeometry args={[0.35, 6, 0.35]} />
            <meshStandardMaterial color={steel} metalness={0.4} roughness={0.5} />
          </mesh>
        ))}

        {/* Loading dock doors on the front wall */}
        {bays.map((x) => (
          <group key={`dock-${x}`} position={[x, 1.9, 4.2]}>
            {/* door frame */}
            <mesh position={[0, 0, 0]}>
              <boxGeometry args={[2.4, 3.6, 0.15]} />
              <meshStandardMaterial color={steel} />
            </mesh>
            {/* door panel */}
            <mesh position={[0, -0.1, 0.09]}>
              <boxGeometry args={[2.1, 3.2, 0.08]} />
              <meshStandardMaterial color="#eef1f3" metalness={0.2} roughness={0.7} />
            </mesh>
            {/* door slat lines */}
            {[-1.2, -0.6, 0, 0.6, 1.2].map((y) => (
              <mesh key={y} position={[0, y, 0.14]}>
                <boxGeometry args={[2.1, 0.04, 0.02]} />
                <meshStandardMaterial color="#b8c0c6" />
              </mesh>
            ))}
          </group>
        ))}
      </group>

      {/* Rooftop HVAC units */}
      {[-4, 0, 4].map((x) => (
        <mesh key={`hvac-${x}`} position={[x, 6.85, -1.5]} castShadow>
          <boxGeometry args={[1.6, 0.7, 1.6]} />
          <meshStandardMaterial color="#9aa6ae" metalness={0.3} roughness={0.6} />
        </mesh>
      ))}

      {/* A couple of pallets/crates inside for scale */}
      {[
        [-5, 0.5, -1.5],
        [-3.5, 0.5, -1.5],
        [5, 0.5, 1.8],
      ].map((p, i) => (
        <mesh key={`crate-${i}`} position={p as [number, number, number]} castShadow>
          <boxGeometry args={[1.2, 1, 1.2]} />
          <meshStandardMaterial color={i === 2 ? accent : "#b98a55"} />
        </mesh>
      ))}
    </group>
  )
}

export function WarehouseModel() {
  return (
    <div className="h-[300px] w-full overflow-hidden rounded-lg border border-[#c8c8c8] bg-[#eef2f5]">
      <Canvas shadows camera={{ position: [16, 11, 16], fov: 40 }} dpr={[1, 2]}>
        <Suspense fallback={null}>
          <color attach="background" args={["#e9edf0"]} />
          <ambientLight intensity={0.6} />
          <directionalLight
            position={[10, 15, 8]}
            intensity={1.1}
            castShadow
            shadow-mapSize={[1024, 1024]}
          />
          <Warehouse />
          <ContactShadows position={[0, 0.02, 0]} opacity={0.4} scale={40} blur={2} far={12} />
          <Environment preset="warehouse" />
          <OrbitControls
            enablePan={false}
            minPolarAngle={0.2}
            maxPolarAngle={Math.PI / 2.2}
            minDistance={14}
            maxDistance={34}
            autoRotate
            autoRotateSpeed={0.8}
          />
        </Suspense>
      </Canvas>
    </div>
  )
}
