import L from 'leaflet';
import ReactDOM from 'ReactDOM';
import React from 'react';
import PropTypes from 'prop-types';
import './Labels.scss';
import LabelsPanel from './LabelsPanel';

class LabelsButton extends React.Component {
  static propTypes = {
    tasks: PropTypes.array.isRequired,
    map: PropTypes.object.isRequired,
    layersControl: PropTypes.object.isRequired
  }

  constructor(props){
    super(props);

    this.state = {
        showPanel: false
    };
  }

  handleOpen = () => {
    this.setState({showPanel: true});
  }

  handleClose = () => {
    this.setState({showPanel: false});
  }

  render(){ 
    const { showPanel } = this.state;

    return (<div className={showPanel ? "open" : ""}>
        <a href="javascript:void(0);" 
            onClick={this.handleOpen} 
            className="leaflet-control-labels-button leaflet-bar-part theme-secondary"></a>
        <LabelsPanel map={this.props.map} layersControl={this.props.layersControl} isShowed={showPanel} tasks={this.props.tasks} onClose={this.handleClose} />
    </div>);
  }
}

export default L.Control.extend({
    options: {
        position: 'topright'
    },

    onAdd: function (map) {
        var container = L.DomUtil.create('div', 'leaflet-control-labels leaflet-bar leaflet-control');
        L.DomEvent.disableClickPropagation(container);
        ReactDOM.render(<LabelsButton map={this.options.map} layersControl={this.options.layersControl} tasks={this.options.tasks} />, container);

        return container;
    }
});

