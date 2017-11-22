fcsApp.controller('QuestionsController', ['$scope', '$http', function ($scope, $http) {

    //$('.modal').fadeIn();

    $scope.new_question = {};
    $scope.new_question.options = [];

    $scope.add_option = function () {
        $scope.new_question.options.push({"title": ""});
    };
    $scope.questions = [];
    $scope.save_question = function () {
        //TODO : MUST HAVE 2 OPTIONS
        $http.post("/admin/questions", $scope.new_question).then(function (response) {
            $scope.gridOptions.data = response.data;
            $('.modal').fadeOut();
            $scope.new_question = {};
            $scope.new_question.options = [];

        }, function (response) {
            alert(response.data);
        })
    }

    $scope.set_active = function (question) {
        $http.post("/admin/questions/activate", {id: question.id}).then(function (response) {
            $scope.gridOptions.data = response.data;

        }, function (response) {
            alert(response.data);
        })
    }
    $scope.delete = function (question) {
        $http.post("/admin/questions/delete", {id: question.id}).then(function (response) {
            $scope.gridOptions.data = response.data;
            console.log($scope.questions);
        }, function (response) {
            alert(response.data);
        })
    }

    $scope.gridOptions = {};
    $scope.gridOptions.columnDefs = [
        {
            name: 'title',
            displayName: 'Question'
        },
        {
            name: 'options_str',
            displayName: 'Options'
        },
        {
            name: 'votes',
            displayName: 'Votes'
        },
        {
            name: 'added',
            displayName: 'Added On'
        },
        {
            field: 'Status',
            displayName: 'Status',
            cellTemplate: '<div class="ui-grid-cell-contents" ><span ng-if="row.entity.is_active" class="label label-success tb">Active</span><span ng-if="!row.entity.is_active" class="label label-danger tb"  ng-click="grid.appScope.set_active(row.entity)">Inactive</span></div>'
        },
        {
            field: 'Remove',
            displayName: 'Remove',
            cellTemplate: '<div class="ui-grid-cell-contents" ><span confirm="Confirm delete?" ng-click="grid.appScope.delete(row.entity)" ng-hide="row.entity.is_active" class="label label-success tb">Delete</span></div>'
        },

    ];
    $http.get("/admin/questions").then(function (response) {
        $scope.gridOptions.data = response.data;
        console.log($scope.questions);

    }, function (response) {
        alert(response.data);

    });

}]);

fcsApp.controller('DashboardController', ['$scope', '$http', '$interval', function ($scope, $http, $interval) {

    $scope.labels = ["Download Sales", "In-Store Sales", "Mail-Order Sales"];
    $scope.data = [300, 500, 100];
    $scope.poll = function () {
        $http.get("/admin/poll").then(function (response) {

            if ($scope.hash == response.data.hash)
                return
            $scope.hash = response.data.hash;
            $scope.questions = response.data.questions;

            for (var i = 0; i < $scope.questions.length; i++) {
                $scope.questions[i].labels = [];
                $scope.questions[i].data = [];
                $scope.questions[i].no_votes = true;

                for (var j = 0; j < $scope.questions[i].options.length; j++) {
                    $scope.questions[i].labels.push($scope.questions[i].options[j].title + " (" + $scope.questions[i].options[j].votes + ")");
                    $scope.questions[i].data.push($scope.questions[i].options[j].votes);
                    $scope.questions[i].no_votes = $scope.questions[i].no_votes * ($scope.questions[i].options[j].votes == 0);

                }
            }
            console.log($scope.questions);
        }, function (response) {
            alert(response.data);

        });

    }
    $scope.poll();
    var stop = $interval(function () {
        $scope.poll()
    }, 3000);
    $scope.$on('$destroy', function () {
        // Make sure that the interval is destroyed too
        $interval.cancel(stop);

    });

}]);