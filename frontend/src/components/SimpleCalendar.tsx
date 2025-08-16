import React, { useState, useEffect } from 'react';
import { diaryAPI, guidedDiaryAPI, unifiedDiaryAPI } from '../utils/api.ts';

interface SimpleCalendarProps {
  language?: string;
  onDateSelect: (date: string, entries: any[]) => void;
  apiEndpoint?: string; // '/diary' for legacy, '/guided-diary' for guided, '/unified-diary' for both (default)
}

const SimpleCalendar: React.FC<SimpleCalendarProps> = ({ 
  language = 'en', 
  onDateSelect, 
  apiEndpoint = '/unified-diary' 
}) => {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [diaryDates, setDiaryDates] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadDiaryDates();
  }, [apiEndpoint]);

  const loadDiaryDates = async () => {
    try {
      let response;
      if (apiEndpoint === '/guided-diary') {
        response = await guidedDiaryAPI.getDates();
      } else if (apiEndpoint === '/diary') {
        response = await diaryAPI.getDates();
      } else {
        // Default to unified diary
        response = await unifiedDiaryAPI.getDates();
      }
      setDiaryDates(response.dates);
    } catch (error) {
      console.error('Error loading diary dates:', error);
    }
  };

  const handleDateClick = async (date: string) => {
    if (!diaryDates.includes(date)) return;
    
    setLoading(true);
    try {
      let response;
      if (apiEndpoint === '/guided-diary') {
        response = await guidedDiaryAPI.getByDate(date);
        onDateSelect(date, response.sessions);
      } else if (apiEndpoint === '/diary') {
        response = await diaryAPI.getByDate(date);
        onDateSelect(date, response.entries);
      } else {
        // Default to unified diary
        response = await unifiedDiaryAPI.getByDate(date);
        onDateSelect(date, response.entries);
      }
    } catch (error) {
      console.error('Error loading diary for date:', error);
    } finally {
      setLoading(false);
    }
  };

  const getDaysInMonth = (year: number, month: number) => {
    return new Date(year, month + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (year: number, month: number) => {
    return new Date(year, month, 1).getDay();
  };

  const formatDate = (year: number, month: number, day: number) => {
    return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
  };

  const renderCalendar = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const daysInMonth = getDaysInMonth(year, month);
    const firstDay = getFirstDayOfMonth(year, month);

    const days = [];
    
    // Empty cells for days before the first day of the month
    for (let i = 0; i < firstDay; i++) {
      days.push(<div key={`empty-${i}`} style={{ padding: '8px' }}></div>);
    }

    // Days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      const dateStr = formatDate(year, month, day);
      const hasDiary = diaryDates.includes(dateStr);
      const isToday = dateStr === new Date().toISOString().split('T')[0];

      days.push(
        <div
          key={day}
          onClick={() => handleDateClick(dateStr)}
          style={{
            padding: '8px',
            textAlign: 'center',
            cursor: hasDiary ? 'pointer' : 'default',
            backgroundColor: isToday ? '#e3f2fd' : 'transparent',
            color: hasDiary ? '#007bff' : (isToday ? '#1976d2' : '#666'),
            fontWeight: hasDiary ? 'bold' : 'normal',
            borderRadius: '4px',
            fontSize: '14px',
            border: hasDiary ? '1px solid #007bff' : '1px solid transparent',
            transition: 'all 0.2s ease',
          }}
          onMouseEnter={(e) => {
            if (hasDiary) {
              e.currentTarget.style.backgroundColor = '#f0f8ff';
            }
          }}
          onMouseLeave={(e) => {
            if (!isToday) {
              e.currentTarget.style.backgroundColor = 'transparent';
            } else {
              e.currentTarget.style.backgroundColor = '#e3f2fd';
            }
          }}
        >
          {day}
        </div>
      );
    }

    return days;
  };

  const previousMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };

  const nextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };

  const monthNames = language === 'en' 
    ? ['January', 'February', 'March', 'April', 'May', 'June',
       'July', 'August', 'September', 'October', 'November', 'December']
    : ['一月', '二月', '三月', '四月', '五月', '六月',
       '七月', '八月', '九月', '十月', '十一月', '十二月'];

  const dayNames = language === 'en' 
    ? ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    : ['日', '一', '二', '三', '四', '五', '六'];

  return (
    <div style={{ 
      backgroundColor: 'white', 
      borderRadius: '10px', 
      padding: '15px',
      border: '1px solid #e0e0e0',
      marginBottom: '20px'
    }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: '15px' 
      }}>
        <button
          onClick={previousMonth}
          style={{
            backgroundColor: 'transparent',
            border: 'none',
            cursor: 'pointer',
            fontSize: '18px',
            color: '#666',
            padding: '5px',
          }}
        >
          ‹
        </button>
        
        <h3 style={{ 
          margin: 0, 
          color: '#333', 
          fontSize: '16px', 
          fontWeight: '600' 
        }}>
          {monthNames[currentDate.getMonth()]} {currentDate.getFullYear()}
        </h3>
        
        <button
          onClick={nextMonth}
          style={{
            backgroundColor: 'transparent',
            border: 'none',
            cursor: 'pointer',
            fontSize: '18px',
            color: '#666',
            padding: '5px',
          }}
        >
          ›
        </button>
      </div>

      {/* Day names header */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(7, 1fr)', 
        gap: '2px',
        marginBottom: '10px'
      }}>
        {dayNames.map(day => (
          <div key={day} style={{ 
            textAlign: 'center', 
            fontWeight: '500', 
            color: '#888',
            fontSize: '12px',
            padding: '8px'
          }}>
            {day}
          </div>
        ))}
      </div>

      {/* Calendar days */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(7, 1fr)', 
        gap: '2px' 
      }}>
        {renderCalendar()}
      </div>

      {/* Legend */}
      <div style={{ 
        marginTop: '15px', 
        fontSize: '12px', 
        color: '#666',
        display: 'flex',
        alignItems: 'center',
        gap: '15px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{
            width: '12px',
            height: '12px',
            border: '1px solid #007bff',
            borderRadius: '2px'
          }}></div>
          <span>{language === 'en' ? 'Has diary' : '有日记'}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '5px' }}>
          <div style={{
            width: '12px',
            height: '12px',
            backgroundColor: '#e3f2fd',
            borderRadius: '2px'
          }}></div>
          <span>{language === 'en' ? 'Today' : '今天'}</span>
        </div>
      </div>

      {loading && (
        <div style={{ 
          textAlign: 'center', 
          marginTop: '10px', 
          color: '#666',
          fontSize: '14px'
        }}>
          {language === 'en' ? 'Loading diary...' : '加载日记中...'}
        </div>
      )}
    </div>
  );
};

export default SimpleCalendar;