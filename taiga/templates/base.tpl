{% macro nav_link(link, text, tooltip) -%}
  {%if tooltop != "" %}
    <li><a class="has-tooltip" href="{{ link }}" data-toggle="tooltip" data-placement="bottom" title="{{ tooltip }}">{{ text }}</a></li>
  {% else %}
    <li><a href="{{ link }}">{{ text }}</a></li>
  {% endif %}
{%- endmacro %}
<!DOCTYPE html>
<html>
  <head>
    {% block head %}
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}{% endblock %}</title>

    <!-- Latest compiled and minified CSS -->
    <link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap.min.css">

    <!-- Optional theme -->
    <link rel="stylesheet" href="//netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap-theme.min.css">

    <link href="//cdnjs.cloudflare.com/ajax/libs/x-editable/1.5.1/bootstrap3-editable/css/bootstrap-editable.css" rel="stylesheet"/>

    <link href="/static/select2-3.4.5/select2.css" rel="stylesheet"/>
    <link href="/static/select2-bootstrap-css/select2-bootstrap.css" rel="stylesheet"/>

    <!-- Latest compiled and minified JavaScript -->

    <!-- HTML5 Shim and Respond.js IE8 support of HTML5 elements and media queries -->
    <!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
    <!--[if lt IE 9]>
      <script src="https://oss.maxcdn.com/libs/html5shiv/3.7.0/html5shiv.js"></script>
      <script src="https://oss.maxcdn.com/libs/respond.js/1.4.2/respond.min.js"></script>
    <![endif]-->

    <!-- need to set width of .input-large for xedit + select2 inline editing of tags-->
    <style>
    .select2-container.input-large {
      width: 260px;
    }
    
    .top-of-page-margin {
      padding-top: 20px;
    }
    </style>
      
    {% endblock %}
  </head>

<body>

  <div class="container">
    <ul class="nav nav-pills top-of-page-margin">
      {{ nav_link("/", "Taiga home", "") }}
      {{ nav_link("/upload/tabular-form", "Upload numerical matrix", "Uploading of a matrix comprising of numerical values with row and column labels") }}
      {{ nav_link("/upload/columnar-form", "Upload table", "Upload a table where some columns can contain non-numeric values") }}
      {{ nav_link("/datasets-by-tag", "List datasets by tag", "") }}
      {{ nav_link("/datasets-by-timestamp", "List datasets by timestamp", "") }}
      {% if is_logged_in %}
        {{ nav_link("/logout", "Logout", "") }}
      {% else %}
        {{ nav_link("/login", "Login", "") }}
      {% endif %}
    </ul>

    {% with messages = get_flashed_messages(with_categories=true) %}
      {% for category, message in messages %}
        <div class="alert alert-{{ category }}">{{ message }}</div>
      {% endfor %}
    {% endwith %}

{% block content %}{% endblock %}
  </div>

  <script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.0/jquery.min.js"></script>
  <script src="//netdna.bootstrapcdn.com/bootstrap/3.1.1/js/bootstrap.min.js"></script>
  <script src="//cdnjs.cloudflare.com/ajax/libs/x-editable/1.5.1/bootstrap3-editable/js/bootstrap-editable.min.js"></script>
  <script src="/static/select2-3.4.5/select2.js"></script>

<script>
  $(document).ready(function() {
    $('.has-tooltip').tooltip({})
  });
</script>

{% block scripts %}
{% endblock %}

</body>
</html>

