import React from 'react'
import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import SouthIndianChart from './SouthIndianChart'

const SAMPLE_POSITIONS = {
  Sun: { sign_index: 1, degree_in_sign: 14.2, nakshatra: 'Rohini', pada: 3, retrograde: false },
  Moon: { sign_index: 4, degree_in_sign: 8.1, nakshatra: 'Magha', pada: 2, retrograde: false },
}

describe('SouthIndianChart classic variant', () => {
  it('shows Tamil rashi labels and fixed sign numbers', () => {
    const { container } = render(
      <SouthIndianChart
        title="D1"
        planetPositions={SAMPLE_POSITIONS}
        lagnaSignIndex={4}
        variant="classic"
        showDetails
        chartKind="natal"
      />,
    )
    expect(screen.getByText('மேஷம்')).toBeInTheDocument()
    expect(screen.getByText('சிம்மம்')).toBeInTheDocument()
    expect(container.querySelector('.si-chart__lagna-badge')).toHaveTextContent('Lagna ↑')
    expect(screen.getByText('Rohini · P3')).toBeInTheDocument()
  })

  it('omits Lagna highlight on transit sky chart', () => {
    const { container } = render(
      <SouthIndianChart
        title="Transit"
        planetPositions={SAMPLE_POSITIONS}
        lagnaSignIndex={4}
        variant="classic"
        showDetails
        chartKind="transit"
      />,
    )
    expect(container.querySelector('.si-chart__lagna-badge')).toBeNull()
    expect(screen.getByText('கோசாரம்')).toBeInTheDocument()
  })

  it('shows Prashna centre label and Lagna badge', () => {
    const { container } = render(
      <SouthIndianChart
        title="Prashna"
        planetPositions={SAMPLE_POSITIONS}
        lagnaSignIndex={4}
        variant="classic"
        showDetails
        chartKind="prashna"
      />,
    )
    expect(screen.getByText('பிரஷ்னா')).toBeInTheDocument()
    expect(container.querySelector('.si-chart__lagna-badge')).toHaveTextContent('Lagna ↑')
  })

  it('shows Dasamsa centre label for D10', () => {
    render(
      <SouthIndianChart
        title="D10"
        planetPositions={SAMPLE_POSITIONS}
        lagnaSignIndex={4}
        variant="classic"
        showDetails
        chartKind="natal"
        dasamsa
      />,
    )
    expect(screen.getByText('தசாம்சம்')).toBeInTheDocument()
  })
})
