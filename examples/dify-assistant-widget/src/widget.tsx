import React from 'react';
import { initializeWidget } from '@apitable/widget-sdk';
import { DifyAssistantWidget } from './DifyAssistantWidget';
import './styles.css';

// 注意：packageId 必须与 widget.config.json 完全一致，否则宿主加载报 PackageIdNotMatch。
initializeWidget(DifyAssistantWidget, 'wpkMatAssist1');
