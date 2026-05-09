import React from 'react';
import { initializeWidget } from '@apitable/widget-sdk';
import { App } from './App';
import './style.css';

initializeWidget(App, process.env.WIDGET_PACKAGE_ID!);
