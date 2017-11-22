// app.js
var fcsApp = angular.module('fcsApp', ['ui.router', 'ui.bootstrap','angular-confirm','ui.grid','chart.js']);

fcsApp.config(function ($stateProvider, $urlRouterProvider) {

    $urlRouterProvider.otherwise('/dashboard');

    $stateProvider

        .state('dashboard', {
            url: '/dashboard',
            templateUrl: 'admin/dashboard.html',
            controller: 'DashboardController'
        })
        .state('questions', {
            url: '/questions',
            templateUrl: 'admin/questions.html',
            controller: 'QuestionsController'
        })

        
        .state('settings', {
            url: '/settings',
            templateUrl: 'admin/settings',  
            controller: 'SettingsController'
        });

});