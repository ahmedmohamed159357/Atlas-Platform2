
import { useState, useEffect } from 'react';
import ForceGraph3D from 'react-force-graph-3d';

const TypedForceGraph3D = ForceGraph3D as any;

// Graph Data Interfaces
interface GraphNode {
    id: string;
    group: number;
    val?: number;
    label?: string;
}

interface GraphLink {
    source: string;
    target: string;
}

interface GraphData {
    nodes: GraphNode[];
    links: GraphLink[];
}

const NeuralMesh = () => {
    const width = window.innerWidth;
    const height = window.innerHeight;
    const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
    const [pulse, setPulse] = useState(false);

    // Fetch Graph Topology from the Hive Mind
    useEffect(() => {
        const fetchTopology = async () => {
            try {
                const res = await fetch("http://localhost:9001/api/graph");
                if (res.ok) {
                    const data = await res.json();
                    setGraphData(data);
                }
            } catch (e) { }
        };

        // Interaction socket for pulses
        const socket = new WebSocket("ws://localhost:9001/api/hive/stream/GLOBAL"); // Placeholder or similar
        // Actually, since we don't have a specific global stream yet, we poll achievements and pulse on change

        fetchTopology();
        const interval = setInterval(fetchTopology, 3000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="fixed inset-0 -z-10 opacity-60">
            <TypedForceGraph3D
                graphData={graphData}
                nodeAutoColorBy="group"
                nodeColor={node => {
                    if (node.id === 'SHADOW_RELAY' && pulse) return '#ffffff';
                    switch (node.group) {
                        case 1: return '#ff003c'; // King
                        case 2: return '#bd00ff'; // Zombie
                        case 3: return '#00ff41'; // Ghost
                        default: return '#00f3ff'; // Target
                    }
                }}
                nodeLabel="label"
                linkColor={link => link.is_shadow ? '#444444' : (link.dashed ? '#00f3ff' : '#ffffff')}
                linkWidth={link => link.is_shadow ? 0.2 : (link.dashed ? 0.3 : 0.5)}
                linkOpacity={link => link.is_shadow ? 0.1 : (link.dashed ? 0.2 : 0.3)}
                linkDashArray={link => link.dashed ? 2 : 0}
                linkDashGap={link => link.dashed ? 1 : 0}
                linkDirectionalArrowLength={link => link.is_shadow ? 0 : 3}
                linkDirectionalArrowRelPos={1}
                linkDirectionalParticles={link => link.is_shadow ? 2 : 0}
                linkDirectionalParticleWidth={0.5}
                linkDirectionalParticleSpeed={0.005}
                backgroundColor="#00000000"
                enableNodeDrag={false}
                showNavInfo={false}
                width={width}
                height={height}
            />
        </div>
    );
};

export default NeuralMesh;
