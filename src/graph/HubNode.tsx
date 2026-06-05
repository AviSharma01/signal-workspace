import { memo } from 'react'
import { Handle, Position } from 'reactflow'
import { TEXT_MUTED } from '../shared/constants'

function HubNode() {
  return (
    <>
      <Handle type="source" position={Position.Right} isConnectable={false} style={{ opacity: 0 }} />
      <div
        style={{
          width: 10,
          height: 10,
          borderRadius: 999,
          backgroundColor: TEXT_MUTED,
        }}
      />
    </>
  )
}

export default memo(HubNode)
