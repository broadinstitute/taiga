{% extends "base.tpl" %}
{% macro bold_if_ref(value) -%}
  {% if value.id %}
    <strong> {{ value.id }} </strong>
  {% else %}
    {{ value }}
  {% endif %}
{%- endmacro %}

{% block title %}Dataset{% endblock %}
{% block content %}
  <a href="/">Home</a>
  <h1>Name: {{ meta.name }}</h1>
  <p> Created by {{ meta.created_by }}</p>
  <p> Description: {{ meta.description }} </p>
  
  <h2>Dimensions</h2>
  
  <table class="table table-bordered table-striped">
    <thead>
      <tr>
          <th></th>
          <th>Description</th>
          <th>Values</th>
      </tr>
    </thead>
    
    <tbody>
      {% for dim in dims %}
        <tr>
          <td>{{ loop.index }}</td>
          <td>{{ dim.name }}</td>
          <td>{{ dim.values|length }}</td>
        </tr>
      {% endfor %}
    </tbody>
  </table>
{% endblock %}