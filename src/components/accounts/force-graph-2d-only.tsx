'use client'

import fromKapsule from 'react-kapsule'
import ForceGraph2DKapsule from 'force-graph'

/**
 * 2D force graph only. Do not use `react-force-graph` from npm — that package imports
 * VR/AR/3D stacks at the top level and throws `AFRAME is not defined` in the browser.
 * Runtime: `force-graph` is a Kapsule factory; published types use a class shape.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const ForceGraph2D = fromKapsule(ForceGraph2DKapsule as any, {
  methodNames: [
    'emitParticle',
    'd3Force',
    'd3ReheatSimulation',
    'stopAnimation',
    'pauseAnimation',
    'resumeAnimation',
    'centerAt',
    'zoom',
    'zoomToFit',
    'getGraphBbox',
    'screen2GraphCoords',
    'graph2ScreenCoords',
  ],
})
ForceGraph2D.displayName = 'ForceGraph2D'
